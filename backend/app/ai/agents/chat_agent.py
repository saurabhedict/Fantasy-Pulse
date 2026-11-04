"""'Ask Pulse' chat agent: a LangGraph ReAct agent whose tools wrap the domain layer."""
import logging

from langgraph.prebuilt import create_react_agent

from app.ai.agents.tools import build_tools
from app.ai.llm import as_text
from app.ai.prompts import chat_system
from app.domain.models import Match

log = logging.getLogger(__name__)


def build_agent(llm, match: Match, step: int, xi: list, captain: str, vc: str):
    roster = ", ".join(f"{p} ({'captain' if p == captain else 'vice-captain' if p == vc else 'player'})"
                       for p in xi)
    return create_react_agent(llm, tools=build_tools(match, step, xi, captain, vc), prompt=chat_system(roster))


def ask_agent(agent, history: list[tuple[str, str]]) -> tuple[str, bool]:
    """history: [(role, text)]. Returns (reply, ok)."""
    try:
        result = agent.invoke({"messages": history}, config={"recursion_limit": 20})
        text = as_text(result["messages"][-1].content).strip()
        # LangGraph returns this sentence (instead of raising) when the step limit is hit mid-tool-loop.
        if text.lower().startswith("sorry, need more steps"):
            return "That question needs too many lookups. Try asking about one player or one thing at a time.", False
        return (text, True) if text else ("I couldn't work that out, try rephrasing.", False)
    except Exception:
        log.warning("chat agent failed", exc_info=True)
        return "Pulse is busy right now. Please try again in a moment.", False
