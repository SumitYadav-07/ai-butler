import httpx

from app.config import get_settings


class AIUnavailable(Exception):
    """The AI service could not be used (not configured, network error, or bad response)."""


def call_llm(system: str, messages: list[dict]) -> str:
    settings = get_settings()
    if not settings.ai_api_key:
        raise AIUnavailable("AI_API_KEY is not configured.")
    try:
        response = httpx.post(
            settings.ai_api_url,
            headers={"x-api-key": settings.ai_api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": settings.ai_model, "max_tokens": 600, "system": system, "messages": messages},
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        raise AIUnavailable(f"Network error: {type(exc).__name__}") from exc
    if response.status_code != 200:
        raise AIUnavailable(f"AI service returned status {response.status_code}.")
    blocks = response.json().get("content", [])
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
    if not text:
        raise AIUnavailable("The AI service returned an empty answer.")
    return text