"""Three separate LLMs (LangChain chat models) behind one container.

llm1 = Groq, llm2 = Gemini, llm3 = Aion Labs. Any of them may be None (no key).
`LLMs.ordered()` gives the configured ones in the priority set by LLM_ORDER; callers try them in turn.
"""
import logging
import os
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings

log = logging.getLogger(__name__)

# public provider name -> attribute on LLMs
_ATTR = {"groq": "llm1", "gemini": "llm2", "aion": "llm3"}


def as_text(content) -> str:
    """Chat models sometimes return a list of parts instead of a string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(p if isinstance(p, str) else p.get("text", "") for p in content)
    return str(content)


@dataclass
class LLMs:
    llm1: Any = None     # Groq
    llm2: Any = None     # Gemini
    llm3: Any = None     # Aion Labs
    order: tuple = ("groq", "gemini", "aion")

    def ordered(self) -> list[tuple[str, Any]]:
        """[(provider_name, model)] for configured models, in priority order."""
        return [(n, getattr(self, _ATTR[n])) for n in self.order
                if n in _ATTR and getattr(self, _ATTR[n]) is not None]

    def __bool__(self) -> bool:
        return bool(self.ordered())


def _make(cls, **kwargs):
    try:
        return cls(**kwargs)
    except Exception:           # older/newer library versions may not accept every kwarg
        kwargs.pop("timeout", None)
        kwargs.pop("max_retries", None)
        return cls(**kwargs)


def build_groq(s: Settings):
    if not s.groq_api_key:
        return None
    try:
        os.environ.setdefault("GROQ_API_KEY", s.groq_api_key)
        from langchain_groq import ChatGroq
        return _make(ChatGroq, model=s.groq_model, temperature=0.2, timeout=s.llm_timeout_s, max_retries=1)
    except Exception:
        log.exception("llm1 (Groq) could not be initialised")
        return None


def build_gemini(s: Settings):
    if not s.google_api_key:
        return None
    try:
        os.environ.setdefault("GOOGLE_API_KEY", s.google_api_key)
        from langchain_google_genai import ChatGoogleGenerativeAI
        return _make(ChatGoogleGenerativeAI, model=s.gemini_model, temperature=0.2,
                     timeout=s.llm_timeout_s, max_retries=1)
    except Exception:
        log.exception("llm2 (Gemini) could not be initialised")
        return None


def build_aion(s: Settings):
    if not s.aion_api_key:
        return None
    try:
        # Aion's API is OpenAI-compatible, so LangChain's ChatOpenAI works with a custom base_url.
        from langchain_openai import ChatOpenAI
        return _make(ChatOpenAI, model=s.aion_model, api_key=s.aion_api_key,
                     base_url=s.aion_base_url, temperature=0.2,
                     timeout=s.llm_timeout_s, max_retries=1)
    except Exception:
        log.exception("llm3 (Aion Labs) could not be initialised")
        return None


def build_llms(s: Settings) -> LLMs:
    llms = LLMs(llm1=build_groq(s), llm2=build_gemini(s), llm3=build_aion(s), order=s.llm_order_list)
    log.info("LLMs ready (in order): %s", [n for n, _ in llms.ordered()] or "none, using templates")
    return llms