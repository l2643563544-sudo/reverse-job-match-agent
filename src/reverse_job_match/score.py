from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from .llm_client import JSONCompleter
from .models import Job
from .profile import JobProfile
from .prompts import SCORE_SYSTEM, SCORE_USER_TEMPLATE


WEIGHTS = {
    "skill_fit": 0.35,
    "direction_fit": 0.30,
    "experience_fit": 0.20,
    "logistics_fit": 0.15,
}


@dataclass(frozen=True)
class ScoredJob:
    job: Job
    match_score: float
    dimensions: dict[str, float]
    reason: str
    matched_skills: list[dict[str, str]]
    gaps: list[str]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.job.to_dict(),
            "match_score": round(self.match_score, 1),
            "dimensions": self.dimensions,
            "reason": self.reason,
            "matched_skills": self.matched_skills,
            "gaps": self.gaps,
            "confidence": round(self.confidence, 2),
        }


def _clamp_score(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("dimension score must be numeric") from exc
    if not 0 <= number <= 100:
        raise ValueError("dimension score must be between 0 and 100")
    return number


def _parse_dimensions(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        raise ValueError("score response is missing dimensions")

    dimensions = {}
    for name in WEIGHTS:
        if name not in raw:
            raise ValueError(f"score response is missing dimension: {name}")
        dimensions[name] = _clamp_score(raw[name])
    return dimensions


def score_from_dict(job: Job, data: dict[str, Any]) -> ScoredJob:
    dimensions = _parse_dimensions(data.get("dimensions"))
    match_score = sum(dimensions[name] * WEIGHTS[name] for name in WEIGHTS)

    confidence = data.get("confidence")
    try:
        confidence = float(confidence)
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence must be numeric") from exc
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")

    matched_skills = data.get("matched_skills", [])
    if not isinstance(matched_skills, list):
        raise ValueError("matched_skills must be a list")

    gaps = data.get("gaps", [])
    if not isinstance(gaps, list) or not all(isinstance(item, str) for item in gaps):
        raise ValueError("gaps must be a list of strings")

    return ScoredJob(
        job=job,
        match_score=match_score,
        dimensions=dimensions,
        reason=str(data.get("reason", "")).strip(),
        matched_skills=matched_skills,
        gaps=gaps,
        confidence=confidence,
    )


def score_job(profile: JobProfile, job: Job, client: JSONCompleter) -> ScoredJob:
    import json

    user_prompt = SCORE_USER_TEMPLATE.format(
        candidate_json=json.dumps(profile.candidate.to_dict(), ensure_ascii=False),
        target_json=json.dumps(profile.target.to_dict(), ensure_ascii=False),
        job_jd=job.jd,
    )
    data = client.complete_json(SCORE_SYSTEM, user_prompt)
    return score_from_dict(job, data)


def score_jobs(
    profile: JobProfile,
    jobs: list[Job],
    client: JSONCompleter,
    min_score: float = 0,
    max_workers: int = 2,
) -> list[ScoredJob]:
    if len(jobs) == 1:
        scored = [score_job(profile, jobs[0], client)]
    else:
        workers = max(1, min(max_workers, len(jobs)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            scored = list(
                executor.map(
                    lambda job: score_job(profile, job, client),
                    jobs,
                )
            )
    scored = [item for item in scored if item.match_score >= min_score]
    return sorted(scored, key=lambda item: item.match_score, reverse=True)
