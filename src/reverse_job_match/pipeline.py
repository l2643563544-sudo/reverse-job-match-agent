from dataclasses import dataclass
from pathlib import Path

from .config import load_llm_settings
from .data_loader import load_jobs
from .llm_client import JSONCompleter, OpenAICompatibleClient
from .mock_client import MockCompleter
from .models import Job
from .profile import JobProfile, build_profile
from .report import write_recommendations
from .score import ScoredJob, score_jobs


@dataclass(frozen=True)
class PipelineResult:
    profile: JobProfile
    jobs: list[Job]
    scored_jobs: list[ScoredJob]
    report_path: Path


def make_client(project_root: Path) -> JSONCompleter:
    settings = load_llm_settings(project_root / ".env")
    if settings.api_key:
        return OpenAICompatibleClient(settings)
    return MockCompleter()


def _filter_by_city(
    profile: JobProfile, scored_jobs: list[ScoredJob]
) -> list[ScoredJob]:
    target_cities = {city.strip() for city in profile.target.cities if city.strip()}
    if not target_cities:
        return scored_jobs
    return [item for item in scored_jobs if item.job.city in target_cities]


def prefilter_candidates(
    profile: JobProfile,
    jobs: list[Job],
    max_candidates: int,
) -> list[Job]:
    target_cities = {city.strip() for city in profile.target.cities if city.strip()}
    if target_cities:
        jobs = [job for job in jobs if job.city in target_cities]

    if len(jobs) <= max_candidates:
        return jobs

    keywords = {
        keyword.strip()
        for keyword in profile.target.track_keywords + profile.candidate.candidate_skills
        if keyword.strip()
    }

    def cheap_rank(job: Job) -> tuple[int, int]:
        text = " ".join(
            [job.title, job.jd, " ".join(job.keywords)]
        ).lower()
        hits = sum(1 for keyword in keywords if keyword.lower() in text)
        return hits, -len(text)

    ranked = sorted(enumerate(jobs), key=lambda item: (cheap_rank(item[1]), -item[0]), reverse=True)
    return [job for _, job in ranked[:max_candidates]]


def run_pipeline(
    mode: str,
    resume_path: Path,
    direction_path: Path,
    reference_jd_path: Path,
    output_path: Path,
    project_root: Path,
    min_score: float = 55,
    top_n: int = 10,
    client: JSONCompleter | None = None,
) -> PipelineResult:
    resume = resume_path.read_text(encoding="utf-8").strip()
    direction = direction_path.read_text(encoding="utf-8").strip()
    reference_jd = reference_jd_path.read_text(encoding="utf-8").strip()

    active_client = client or make_client(project_root)
    profile = build_profile(resume, direction, reference_jd, active_client)

    if mode == "live":
        from .collector_adapter import collect_live_jobs

        city = profile.target.cities[0] if profile.target.cities else "上海"
        jobs = collect_live_jobs(
            profile.target.track_keywords,
            city,
            project_root=project_root,
        )
        source_label = "live"
    else:
        jobs = load_jobs(project_root / "data" / "jobs_fixture.json")
        source_label = "fixture-demo"

    candidates = prefilter_candidates(
        profile,
        jobs,
        max_candidates=max(5, min(top_n, 5)),
    )
    scored = score_jobs(profile, candidates, active_client, min_score=min_score)
    scored = _filter_by_city(profile, scored)
    scored = scored[:top_n]

    report_path = write_recommendations(
        profile=profile,
        scored_jobs=scored,
        source_label=source_label,
        input_summary={
            "resume": str(resume_path),
            "direction": str(direction_path),
            "reference_jd": str(reference_jd_path),
        },
        output_path=output_path,
    )

    return PipelineResult(
        profile=profile,
        jobs=jobs,
        scored_jobs=scored,
        report_path=report_path,
    )
