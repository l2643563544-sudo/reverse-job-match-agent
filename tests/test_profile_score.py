import unittest

from reverse_job_match.data_loader import load_jobs
from reverse_job_match.models import Job
from reverse_job_match.profile import build_profile
from reverse_job_match.prompts import PROFILE_SYSTEM
from reverse_job_match.score import score_job


class FakeCompleter:
    def complete_json(
        self, system_prompt: str, user_prompt: str, temperature: float | None = None
    ) -> dict:
        if system_prompt == PROFILE_SYSTEM:
            return {
                "target_role": "产品运营实习生",
                "target_role_summary": "负责用户运营、内容运营和活动运营",
                "track_keywords": ["产品运营", "用户运营", "内容运营"],
                "cities": ["上海", "深圳"],
                "salary_expectation": "150-250元/天",
                "experience_level": "实习/应届",
                "must_have_requirements": ["本科", "沟通能力"],
                "candidate_summary": "有社群运营、内容策划和基础数据分析经验",
                "candidate_skills": ["Excel", "用户运营", "内容运营"],
                "candidate_experiences": ["学生社群运营", "问卷数据分析"],
                "candidate_constraints": "实习岗位",
            }

        return {
            "dimensions": {
                "skill_fit": 80,
                "direction_fit": 70,
                "experience_fit": 60,
                "logistics_fit": 90,
            },
            "matched_skills": [
                {
                    "skill": "用户运营",
                    "candidate_evidence": "有学生社群运营经历",
                    "job_evidence": "要求负责用户运营活动",
                }
            ],
            "gaps": ["缺少正式产品实习经历"],
            "reason": "岗位方向一致，基础运营能力匹配，但正式实习经历较少。",
            "confidence": 0.8,
        }


class ProfileScoreTests(unittest.TestCase):
    def test_build_profile_and_score_fixture_job(self):
        client = FakeCompleter()
        profile = build_profile("示例简历", "产品运营", "参考JD", client)

        self.assertEqual(profile.target.target_role, "产品运营实习生")
        self.assertIn("用户运营", profile.candidate.candidate_skills)

        jobs = load_jobs("data/jobs_fixture.json")
        first_job = jobs[0]
        scored = score_job(profile, first_job, client)

        self.assertAlmostEqual(scored.match_score, 74.5)
        self.assertEqual(scored.job.job_id, first_job.job_id)
        self.assertEqual(scored.confidence, 0.8)


if __name__ == "__main__":
    unittest.main()
