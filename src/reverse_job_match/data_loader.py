import json
from pathlib import Path

from .models import Job, job_from_dict


def load_jobs(path: Path | str) -> list[Job]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))

    if isinstance(payload, list):
        raw_jobs = payload
    elif isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        raw_jobs = payload["jobs"]
    else:
        raise ValueError("job data must be a list or an object containing a jobs list")

    jobs = [job_from_dict(item) for item in raw_jobs]

    job_ids = [job.job_id for job in jobs]
    if len(job_ids) != len(set(job_ids)):
        raise ValueError("job_id values must be unique")

    return jobs
