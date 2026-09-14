import json
import re

from .prompts import PROFILE_SYSTEM


def _extract_block(text: str, label: str) -> str:
    pattern = rf"{re.escape(label)}\s*\n(.*?)(?=\n\n【|\Z)"
    match = re.search(pattern, text, flags=re.S)
    if not match:
        return ""
    return match.group(1).strip()


def _extract_profile_section(user_prompt: str) -> dict:
    direction = _extract_block(user_prompt, "【目标岗位方向】")
    resume = _extract_block(user_prompt, "【候选人简历】")
    reference_jd = _extract_block(user_prompt, "【目标JD参考】")

    city_candidates = ["上海", "北京", "深圳", "广州", "杭州", "成都", "武汉", "南京", "苏州"]
    cities = [city for city in city_candidates if city in direction]

    salary_match = re.search(r"\d+\s*-\s*\d+\s*元/天", direction)
    salary = salary_match.group(0) if salary_match else "150-250元/天"

    target_role_match = re.search(r"^#+\s*(.+)$", direction, flags=re.M)
    target_role = target_role_match.group(1).strip() if target_role_match else "产品运营实习生"
    if not target_role:
        target_role = "产品运营实习生"

    skills = []
    skill_section = re.search(r"##\s*技能\s*\n(.*)", resume, flags=re.S)
    if skill_section:
        for line in skill_section.group(1).splitlines():
            if line.strip().startswith("-"):
                skills.append(line.strip().lstrip("-").strip())

    skill_keywords = ["用户运营", "内容运营", "活动运营", "社群运营", "数据分析", "Excel"]
    skills.extend(
        item for item in skill_keywords if item in resume and item not in skills
    )

    experiences = []
    experience_section = re.search(
        r"##\s*相关经历\s*\n(.*?)(?=\n##|\Z)", resume, flags=re.S
    )
    if experience_section:
        experiences = [
            line.strip().lstrip("-").strip()
            for line in experience_section.group(1).splitlines()
            if line.strip().startswith("-")
        ]

    return {
        "target_role": target_role,
        "target_role_summary": direction,
        "track_keywords": ["产品运营", "用户运营", "内容运营", "活动运营"],
        "cities": cities,
        "salary_expectation": salary,
        "experience_level": "实习/应届",
        "must_have_requirements": ["本科及以上", "沟通能力", "常用办公软件"],
        "candidate_summary": "有社群运营、内容策划和基础数据分析经验，目标岗位为产品运营实习。",
        "candidate_skills": skills or ["Excel", "用户运营", "内容运营"],
        "candidate_experiences": experiences or ["学生社群运营", "问卷数据分析"],
        "candidate_constraints": "实习岗位",
    }


class MockCompleter:
    """Rule-based completer used when no LLM key is configured."""

    def complete_json(
        self, system_prompt: str, user_prompt: str, temperature: float | None = None
    ) -> dict:
        if system_prompt == PROFILE_SYSTEM:
            return _extract_profile_section(user_prompt)

        candidate_json = _extract_block(user_prompt, "【候选人证据】")
        job_jd = _extract_block(user_prompt, "【岗位JD】")
        candidate_data = json.loads(candidate_json or "{}")
        skills = candidate_data.get("candidate_skills", [])
        matched_skills = [skill for skill in skills if skill and skill in job_jd]

        skill_fit = min(100, 40 + len(matched_skills) * 18)
        direction_fit = 82 if any(
            keyword in job_jd
            for keyword in ["产品运营", "用户运营", "内容运营", "活动运营"]
        ) else 55

        matched_evidence = [
            {
                "skill": skill,
                "candidate_evidence": "简历中提及该技能",
                "job_evidence": "岗位 JD 中包含该技能相关表述",
            }
            for skill in matched_skills
        ]

        return {
            "dimensions": {
                "skill_fit": skill_fit,
                "direction_fit": direction_fit,
                "experience_fit": 65,
                "logistics_fit": 85,
            },
            "matched_skills": matched_evidence,
            "gaps": ["缺少正式产品运营实习经历"],
            "reason": "岗位方向与目标一致，基础运营能力有部分匹配，但正式实习经历较少。",
            "confidence": 0.72,
        }
