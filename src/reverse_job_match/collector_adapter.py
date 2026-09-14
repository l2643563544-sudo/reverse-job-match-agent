import json
import os
import subprocess
import sys
from pathlib import Path

from .models import Job, job_from_dict


class CollectorUnavailableError(RuntimeError):
    pass


def _vendor_dir(project_root: Path) -> Path:
    return project_root / "vendor" / "boss-zhipin-scraper"


def _collector_script(project_root: Path) -> Path:
    script = _vendor_dir(project_root) / "scripts" / "boss_cdp_raw.py"
    if not script.exists():
        raise CollectorUnavailableError(
            "Real-time collection is not ready because the upstream collector is missing."
        )
    return script


def _collector_port() -> str:
    return os.getenv("COLLECTOR_CDP_PORT", "9223").strip()


def _run_collector_command(
    project_root: Path, args: list[str]
) -> subprocess.CompletedProcess:
    script = _collector_script(project_root)
    output_encoding = "gbk" if sys.platform == "win32" else "utf-8"
    try:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=_vendor_dir(project_root),
            capture_output=True,
            text=True,
            encoding=output_encoding,
            errors="replace",
            timeout=900,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CollectorUnavailableError("Real-time collection timed out.") from exc


def _normalize_job(
    raw: dict,
    details_by_id: dict[str, dict],
    source_label: str,
    collected_at: str = "",
) -> Job:
    job_id = str(raw.get("job_id") or raw.get("job_link") or "").strip()
    if not job_id:
        raise ValueError("live job is missing job_id")

    detail = details_by_id.get(job_id, {})
    tags = str(raw.get("tags", "") or "")
    education = "本科" if "本科" in tags else "不限"
    skills = [
        item.strip()
        for item in str(raw.get("skills", "")).split("|")
        if item.strip()
    ]

    source_jd = str(detail.get("jd", "")).strip() or " | ".join(
        value
        for value in (
            str(raw.get("title", "")).strip(),
            str(raw.get("tags", "")).strip(),
            str(raw.get("skills", "")).strip(),
            str(raw.get("job_labels", "")).strip(),
        )
        if value
    )

    return job_from_dict(
        {
            "job_id": job_id,
            "title": str(raw.get("title", "")).strip(),
            "company": str(raw.get("boss_name", "")).strip(),
            "city": str(raw.get("location", "")).split("·", 1)[0].strip(),
            "salary": str(raw.get("salary", "")).strip(),
            "experience": tags,
            "education": education,
            "jd": source_jd,
            "url": str(raw.get("job_link", "")).strip(),
            "keywords": skills,
            "source_label": source_label,
            "collected_at": collected_at,
        }
    )


def collect_live_jobs(
    keywords: list[str],
    city: str,
    pages: int = 1,
    project_root: Path | None = None,
) -> list[Job]:
    """Run a read-only, low-frequency real-time collection.

    This function only fetches search results and job details. It never sends
    messages, greetings, applications, or any other write action.
    """
    root = project_root or Path.cwd()
    _collector_script(root)

    keyword = keywords[0] if keywords else "产品运营"
    city = city or "上海"
    pages = max(1, min(int(pages), 1))

    list_path = root / "data" / "raw" / "boss_jobs_live.json"
    list_path.parent.mkdir(parents=True, exist_ok=True)

    result = _run_collector_command(
        root,
        [
            "--keyword",
            keyword,
            "--city",
            city,
            "--pages",
            str(pages),
            "--output",
            str(list_path),
            "--no-detail",
            "--format",
            "json",
            "--cdp-port",
            _collector_port(),
        ],
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise CollectorUnavailableError(
            "Real-time collection failed. "
            f"Collector output: {detail[:400]}"
        )

    if not list_path.exists():
        raise CollectorUnavailableError("Collector did not create the list output file.")

    list_payload = json.loads(list_path.read_text(encoding="utf-8"))
    raw_jobs = list_payload.get("jobs") if isinstance(list_payload, dict) else list_payload
    if not isinstance(raw_jobs, list) or not raw_jobs:
        raise CollectorUnavailableError("Collector returned no jobs.")

    collected_at = str(list_payload.get("scraped_at", "") or _current_timestamp())
    details_by_id: dict[str, dict] = {}
    jobs = []
    for raw in raw_jobs:
        if not isinstance(raw, dict):
            continue
        try:
            jobs.append(
                _normalize_job(
                    raw,
                    details_by_id,
                    source_label="live",
                    collected_at=collected_at,
                )
            )
        except ValueError:
            continue

    if not jobs:
        raise CollectorUnavailableError("No valid jobs could be normalized from live data.")

    normalized_path = root / "data" / "jobs_live.json"
    normalized_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_label": "live",
                "collected_at": collected_at,
                "jobs": [job.to_dict() for job in jobs],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return jobs


def _current_timestamp() -> str:
    from datetime import datetime

    return datetime.now().astimezone().isoformat(timespec="seconds")
