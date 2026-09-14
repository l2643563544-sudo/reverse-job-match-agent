from pathlib import Path

from .profile import JobProfile
from .score import ScoredJob


def render_markdown(
    profile: JobProfile,
    scored_jobs: list[ScoredJob],
    source_label: str,
    input_summary: dict[str, str],
) -> str:
    lines = [
        "# 求职岗位推荐清单",
        "",
        f"- 目标岗位：{profile.target.target_role}",
        f"- 意向城市：{', '.join(profile.target.cities) or '不限'}",
        f"- 数据来源：{source_label}",
        f"- 推荐数量：{len(scored_jobs)}",
        "",
        "## 推荐结果",
        "",
        "| 排名 | 岗位 | 公司 | 城市 | 薪资 | 匹配分 | 推荐理由 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for index, item in enumerate(scored_jobs, start=1):
        job = item.job
        lines.append(
            f"| {index} | {job.title} | {job.company} | {job.city} | "
            f"{job.salary} | {item.match_score:.1f} | {item.reason} |"
        )

    lines.extend(
        [
            "",
            "## 输入摘要",
            "",
            "- 简历文件：" + input_summary.get("resume", ""),
            "- 目标方向文件：" + input_summary.get("direction", ""),
            "- 参考 JD 文件：" + input_summary.get("reference_jd", ""),
            "",
        ]
    )
    return "\n".join(lines)


def write_recommendations(
    profile: JobProfile,
    scored_jobs: list[ScoredJob],
    source_label: str,
    input_summary: dict[str, str],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_markdown(profile, scored_jobs, source_label, input_summary),
        encoding="utf-8",
    )
    return output_path
