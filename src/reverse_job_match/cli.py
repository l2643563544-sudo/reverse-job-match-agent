import argparse
from pathlib import Path
import sys

from .collector_adapter import CollectorUnavailableError
from .pipeline import run_pipeline


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a reverse job matching recommendation demo."
    )
    parser.add_argument(
        "--mode",
        choices=["demo", "live"],
        default="demo",
        help="demo uses fixed sample jobs; live uses collected data when available",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        default=Path("data/demo_resume.md"),
        help="path to resume text",
    )
    parser.add_argument(
        "--direction",
        type=Path,
        default=Path("data/demo_direction.txt"),
        help="path to target direction text",
    )
    parser.add_argument(
        "--jd",
        type=Path,
        default=Path("data/demo_reference_jd.md"),
        help="path to reference JD text",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=55,
        help="minimum match score to include",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="maximum number of jobs to include",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/recommendations.md"),
        help="output markdown path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = _project_root()

    try:
        result = run_pipeline(
            mode=args.mode,
            resume_path=args.resume,
            direction_path=args.direction,
            reference_jd_path=args.jd,
            output_path=args.output,
            project_root=root,
            min_score=args.min_score,
            top_n=args.top,
        )
    except CollectorUnavailableError as exc:
        print(f"[blocked] {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(f"Generated {len(result.scored_jobs)} recommendations.")
    print(f"Report: {result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
