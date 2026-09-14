from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Job:
    job_id: str
    title: str
    company: str
    city: str
    salary: str
    experience: str
    education: str
    jd: str
    url: str
    keywords: list[str] = field(default_factory=list)
    source_label: str = "fixture"
    collected_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "city": self.city,
            "salary": self.salary,
            "experience": self.experience,
            "education": self.education,
            "jd": self.jd,
            "url": self.url,
            "keywords": list(self.keywords),
            "source_label": self.source_label,
            "collected_at": self.collected_at,
        }


REQUIRED_JOB_FIELDS = (
    "job_id",
    "title",
    "company",
    "city",
    "salary",
    "experience",
    "education",
    "jd",
    "url",
)


def job_from_dict(data: dict[str, Any]) -> Job:
    missing = [name for name in REQUIRED_JOB_FIELDS if name not in data]
    if missing:
        raise ValueError(f"missing required job fields: {', '.join(missing)}")

    keywords = data.get("keywords", [])
    if not isinstance(keywords, list) or not all(
        isinstance(item, str) for item in keywords
    ):
        raise ValueError("keywords must be a list of strings")

    for name in REQUIRED_JOB_FIELDS:
        if not isinstance(data[name], str) or not data[name].strip():
            raise ValueError(f"field must be a non-empty string: {name}")

    return Job(
        job_id=data["job_id"].strip(),
        title=data["title"].strip(),
        company=data["company"].strip(),
        city=data["city"].strip(),
        salary=data["salary"].strip(),
        experience=data["experience"].strip(),
        education=data["education"].strip(),
        jd=data["jd"].strip(),
        url=data["url"].strip(),
        keywords=[item.strip() for item in keywords],
        source_label=str(data.get("source_label", "fixture")).strip(),
        collected_at=str(data.get("collected_at", "")).strip(),
    )
