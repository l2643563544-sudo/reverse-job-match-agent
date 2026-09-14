import json


def extract_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```")
        cleaned = cleaned.removeprefix("json").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

    start = cleaned.find("{")
    if start == -1:
        raise ValueError("response does not contain a JSON object")

    try:
        value, _ = json.JSONDecoder().raw_decode(cleaned[start:])
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON response: {exc}") from exc

    if not isinstance(value, dict):
        raise ValueError("response JSON must be an object")

    return value
