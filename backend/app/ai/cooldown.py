"""Skip a rate-limited LLM for a short time, so every request doesn't waste a failed call on it."""
import time

COOLDOWN_S = 60
_until: dict[str, float] = {}


def is_rate_limited_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    return "429" in text or "ratelimit" in text or "rate limit" in text or "too many requests" in text


def cooling(name: str) -> bool:
    return _until.get(name, 0.0) > time.time()


def mark_failed(name: str, exc: Exception) -> None:
    if is_rate_limited_error(exc):
        _until[name] = time.time() + COOLDOWN_S