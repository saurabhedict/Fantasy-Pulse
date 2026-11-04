"""Ask the LLMs to explain one fact sheet: try each in order, then fall back to a template."""
import json
import logging
from collections import OrderedDict

from app.ai.cooldown import cooling, mark_failed
from app.ai.fallback import template_explanation
from app.ai.llm import as_text
from app.ai.prompts import PULSE_SYSTEM

log = logging.getLogger(__name__)
_CACHE: "OrderedDict[str, tuple[str, str]]" = OrderedDict()
_MAX = 512


def explain(ctx: dict, llms) -> tuple[str, str, str | None]:
    """Return (text, source, provider). source is 'ai' or 'template'; provider is e.g. 'groq' or None."""
    models = llms.ordered() if llms else []
    if not models:
        return template_explanation(ctx), "template", None
    key = json.dumps(ctx, sort_keys=True)
    if key in _CACHE:
        _CACHE.move_to_end(key)
        text, provider = _CACHE[key]
        return text, "ai", provider
    for name, model in models:
        if cooling(name):
            continue                      # recently rate-limited, don't waste a call
        try:
            text = as_text(model.invoke([("system", PULSE_SYSTEM), ("user", key)]).content).strip()
            if not text:
                raise ValueError("empty LLM response")
            _CACHE[key] = (text, name)
            if len(_CACHE) > _MAX:
                _CACHE.popitem(last=False)
            return text, "ai", name
        except Exception as exc:
            mark_failed(name, exc)
            log.warning("LLM '%s' failed for the explanation (%s); trying the next one", name, type(exc).__name__)
    return template_explanation(ctx), "template", None