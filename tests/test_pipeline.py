import tempfile
import unittest
from pathlib import Path

from reverse_job_match.mock_client import MockCompleter
from reverse_job_match.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_demo_pipeline_creates_report(self):
        root = Path(".").resolve()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "recommendations.md"
            result = run_pipeline(
                mode="demo",
                resume_path=root / "data" / "demo_resume.md",
                direction_path=root / "data" / "demo_direction.txt",
                reference_jd_path=root / "data" / "demo_reference_jd.md",
                output_path=output,
                project_root=root,
                client=MockCompleter(),
                top_n=10,
            )

            self.assertTrue(output.exists())
            self.assertLessEqual(len(result.scored_jobs), 10)
            self.assertIn("求职岗位推荐清单", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
