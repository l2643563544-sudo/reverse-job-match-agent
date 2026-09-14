import json
import time
import urllib.error
import urllib.request
from typing import Protocol

from .config import LLMSettings
from .json_utils import extract_json_object


class LLMError(RuntimeError):
    pass


class JSONCompleter(Protocol):
    def complete_json(
        self, system_prompt: str, user_prompt: str, temperature: float | None = None
    ) -> dict:
        ...


class OpenAICompatibleClient:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def complete_json(
        self, system_prompt: str, user_prompt: str, temperature: float | None = None
    ) -> dict:
        if not self.settings.api_key:
            raise LLMError("LLM_API_KEY is not configured")

        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": (
                self.settings.temperature if temperature is None else temperature
            ),
            "response_format": {"type": "json_object"},
        }

        url = self.settings.base_url.rstrip("/") + "/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        last_error: LLMError | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last_error = LLMError(
                    f"LLM request failed with HTTP {exc.code}: {detail}"
                )
                if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise last_error from exc
                time.sleep(1.2 * (attempt + 1))
            except urllib.error.URLError as exc:
                last_error = LLMError(f"LLM request failed: {exc.reason}")
                if attempt == 2:
                    raise last_error from exc
                time.sleep(1.2 * (attempt + 1))

        if last_error is not None:
            raise last_error

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("LLM response is missing choices or message content") from exc

        try:
            return extract_json_object(content)
        except ValueError as exc:
            raise LLMError(str(exc)) from exc
