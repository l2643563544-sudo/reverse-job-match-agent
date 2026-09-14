import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reverse_job_match.collector_adapter import _normalize_job


def main() -> int:
    list_path = ROOT / "data" / "raw" / "boss_jobs_live.json"
    detail_path = ROOT / "data" / "raw" / "boss_details_live.json"
    output_path = ROOT / "data" / "jobs_live.json"

    raw_jobs = json.loads(list_path.read_text(encoding="utf-8")).get("jobs", [])
    list_payload = json.loads(list_path.read_text(encoding="utf-8"))
    raw_jobs = list_payload.get("jobs", [])
    collected_at = str(list_payload.get("scraped_at", ""))
    raw_details = json.loads(detail_path.read_text(encoding="utf-8"))
    details_by_id = {
        str(item.get("job_id", "")): item
        for item in raw_details
        if isinstance(item, dict) and item.get("job_id")
    }

    jobs = []
    for raw in raw_jobs:
        if not isinstance(raw, dict):
            continue
        try:
            jobs.append(
                _normalize_job(
                    raw,
                    details_by_id,
                    "live",
                    collected_at=collected_at,
                ).to_dict()
            )
        except ValueError:
            continue

    output_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_label": "live",
                "collected_at": collected_at,
                "jobs": jobs,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Imported {len(jobs)} live jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
