from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    base_url: str
    model: str
    temperature: float


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            __import__("os").environ.setdefault(key, value)


def load_llm_settings(env_path: Path | str | None = None) -> LLMSettings:
    if env_path is None:
        env_path = Path(".env")
    _load_env_file(Path(env_path))

    import os

    return LLMSettings(
        api_key=os.getenv("LLM_API_KEY", "").strip(),
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip(),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini").strip(),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
    )
