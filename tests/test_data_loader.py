import json
import tempfile
import unittest
from pathlib import Path

from reverse_job_match.data_loader import load_jobs


class LoadJobsTests(unittest.TestCase):
    def test_loads_fixture_with_expected_count(self):
        path = Path("data/jobs_fixture.json").resolve()
        jobs = load_jobs(path)

        self.assertEqual(len(jobs), 20)
        self.assertEqual(len({job.job_id for job in jobs}), 20)
        self.assertTrue(all(job.title and job.jd and job.url for job in jobs))

    def test_rejects_missing_required_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            path.write_text(
                json.dumps([{"job_id": "bad", "title": "产品运营实习生"}]),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing required job fields"):
                load_jobs(path)


if __name__ == "__main__":
    unittest.main()
