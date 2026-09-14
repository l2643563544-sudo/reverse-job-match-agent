from dataclasses import asdict, dataclass, field
from typing import Any

from .llm_client import JSONCompleter
from .prompts import PROFILE_SYSTEM, PROFILE_USER_TEMPLATE


@dataclass(frozen=True)
class TargetRoleSpec:
    target_role: str
    target_role_summary: str
    track_keywords: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    salary_expectation: str = ""
    experience_level: str = ""
    must_have_requirements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateEvidence:
    candidate_summary: str
    candidate_skills: list[str] = field(default_factory=list)
    candidate_experiences: list[str] = field(default_factory=list)
    candidate_constraints: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JobProfile:
    target: TargetRoleSpec
    candidate: CandidateEvidence


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def profile_from_dict(data: dict[str, Any]) -> JobProfile:
    target = TargetRoleSpec(
        target_role=str(data.get("target_role", "")).strip(),
        target_role_summary=str(data.get("target_role_summary", "")).strip(),
        track_keywords=_as_string_list(data.get("track_keywords")),
        cities=_as_string_list(data.get("cities")),
        salary_expectation=str(data.get("salary_expectation", "")).strip(),
        experience_level=str(data.get("experience_level", "")).strip(),
        must_have_requirements=_as_string_list(data.get("must_have_requirements")),
    )
    candidate = CandidateEvidence(
        candidate_summary=str(data.get("candidate_summary", "")).strip(),
        candidate_skills=_as_string_list(data.get("candidate_skills")),
        candidate_experiences=_as_string_list(data.get("candidate_experiences")),
        candidate_constraints=str(data.get("candidate_constraints", "")).strip(),
    )

    if not target.target_role and not candidate.candidate_summary:
        raise ValueError("profile response is missing target role and candidate summary")

    return JobProfile(target=target, candidate=candidate)


def build_profile(
    resume: str,
    direction: str,
    reference_jd: str,
    client: JSONCompleter,
) -> JobProfile:
    user_prompt = PROFILE_USER_TEMPLATE.format(
        resume=resume,
        direction=direction,
        reference_jd=reference_jd,
    )
    data = client.complete_json(PROFILE_SYSTEM, user_prompt)
    return profile_from_dict(data)
