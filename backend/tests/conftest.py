import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from app.ai.llm import LLMs
from app.api.deps import get_llms
from app.main import app

MATCH = "sample_match"


class ToolFake(FakeMessagesListChatModel):
    """Fake chat model that tolerates bind_tools(), so the ReAct agent loop can run offline."""
    def bind_tools(self, tools, **kwargs):
        return self


@pytest.fixture
def no_llm():
    app.dependency_overrides[get_llms] = lambda: LLMs()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(no_llm):
    return TestClient(app)


@pytest.fixture
def team(client):
    r = client.get(f"/matches/{MATCH}/sample-team")
    assert r.status_code == 200
    t = r.json()
    return {"match_id": MATCH, "xi": t["xi"], "captain": t["captain"], "vc": t["vc"]}


def use_llm(model):
    """Install a single fake model as llm1."""
    app.dependency_overrides[get_llms] = lambda: LLMs(llm1=model)


def use_llms(**kw):
    """Install several fake models, e.g. use_llms(llm1=a, llm2=b, order=('gemini', 'groq'))."""
    app.dependency_overrides[get_llms] = lambda: LLMs(**kw)


class Boom(FakeMessagesListChatModel):
    """A model whose every call fails (simulates a 404 / rate limit)."""
    def _generate(self, *a, **k):
        raise RuntimeError("boom")

    def bind_tools(self, tools, **kwargs):
        return self


@pytest.fixture
def fake_explainer():
    use_llm(FakeMessagesListChatModel(responses=[AIMessage(content="Fake AI explanation.")]))
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def fake_agent():
    use_llm(ToolFake(responses=[
        AIMessage(content="", tool_calls=[{"name": "get_team_points", "args": {}, "id": "c1", "type": "tool_call"}]),
        AIMessage(content="Your team is on a fine total."),
    ]))
    yield
    app.dependency_overrides.clear()