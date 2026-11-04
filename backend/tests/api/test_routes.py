from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from app.main import app
from tests.conftest import MATCH, Boom, ToolFake, use_llm, use_llms


def _fake(text):
    return FakeMessagesListChatModel(responses=[AIMessage(content=text)])


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "llm_configured": False, "providers": []}


def test_matches_list_and_detail(client):
    lst = client.get("/matches").json()
    assert any(m["id"] == MATCH for m in lst)
    d = client.get(f"/matches/{MATCH}").json()
    assert d["total_steps"] == len(d["step_labels"]) >= 30 and len(d["players"]) == 22


def test_unknown_match_404_and_path_traversal(client):
    assert client.get("/matches/nope").status_code == 404
    assert client.get("/matches/..%2Fsecret").status_code in (404, 422)


def test_sample_team_is_valid(team):
    assert len(set(team["xi"])) == 11 and team["captain"] != team["vc"]


def test_pulse_template_fallback(client, team):
    r = client.post("/pulse", json={**team, "step": 5})
    assert r.status_code == 200
    b = r.json()
    assert b["source"] == "template" and b["step"] == 5 and len(b["history"]) == 5
    assert b["history"][-1] == b["fan_total"]


def test_pulse_second_innings_has_chase_info(client, team):
    d = client.get(f"/matches/{MATCH}").json()
    step = d["total_steps"] - 5
    b = client.post("/pulse", json={**team, "step": step}).json()
    assert b["scoreboard"]["inning"] == 2 and b["scoreboard"]["target"] > 0


def test_pulse_with_llm_marks_source_ai(client, team, fake_explainer):
    b = client.post("/pulse", json={**team, "step": 7}).json()
    assert b["source"] == "ai" and b["explanation"] == "Fake AI explanation."


def test_pulse_big_swing_flag(client, team):
    d = client.get(f"/matches/{MATCH}").json()
    flags = [client.post("/pulse", json={**team, "step": s}).json()["big_swing"]
             for s in range(1, d["total_steps"] + 1)]
    assert any(flags) and not all(flags)


def test_pulse_validation_errors(client, team):
    assert client.post("/pulse", json={**team, "step": 9999}).status_code == 422
    assert client.post("/pulse", json={**team, "step": 0}).status_code == 422
    assert client.post("/pulse", json={**team, "vc": team["captain"], "step": 3}).status_code == 422
    assert client.post("/pulse", json={**team, "xi": team["xi"][:10], "step": 3}).status_code == 422
    bad = {**team, "xi": team["xi"][:10] + ["Not A Player"], "step": 3}
    assert client.post("/pulse", json=bad).status_code == 422
    assert client.post("/pulse", json={**team, "match_id": "nope", "step": 3}).status_code == 404


def test_chat_without_llm_is_503(client, team):
    r = client.post("/chat", json={**team, "step": 5, "messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 503


def test_chat_agent_calls_tool_and_answers(client, team, fake_agent):
    r = client.post("/chat", json={**team, "step": 5, "messages": [{"role": "user", "content": "my points?"}]})
    assert r.status_code == 200
    assert r.json() == {"reply": "Your team is on a fine total.", "provider": "groq", "degraded": False}


def test_chat_last_message_must_be_user(client, team):
    msgs = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    assert client.post("/chat", json={**team, "step": 5, "messages": msgs}).status_code == 422


def test_chat_step_limit_message_is_reported_as_degraded(client, team):
    # a model that calls a tool forever -> LangGraph hits the step limit
    loop = [AIMessage(content="", id=f"m{i}",
                      tool_calls=[{"name": "get_team_points", "args": {}, "id": f"c{i}", "type": "tool_call"}])
            for i in range(60)]
    use_llm(ToolFake(responses=loop))
    try:
        r = client.post("/chat", json={**team, "step": 5, "messages": [{"role": "user", "content": "q"}]})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200 and r.json()["degraded"] is True
    assert "too many lookups" in r.json()["reply"]


# ---------- three-LLM behaviour ----------

def test_pulse_falls_back_from_llm1_to_llm2(client, team):
    use_llms(llm1=Boom(responses=[]), llm2=_fake("From Gemini."))
    try:
        b = client.post("/pulse", json={**team, "step": 11}).json()
    finally:
        app.dependency_overrides.clear()
    assert b["source"] == "ai" and b["provider"] == "gemini" and b["explanation"] == "From Gemini."


def test_llm_order_setting_controls_priority(client, team):
    use_llms(llm1=_fake("From Groq."), llm3=_fake("From Aion."), order=("aion", "groq"))
    try:
        b = client.post("/pulse", json={**team, "step": 12}).json()
        h = client.get("/health").json()
    finally:
        app.dependency_overrides.clear()
    assert b["provider"] == "aion" and h["providers"] == ["aion", "groq"]


def test_all_llms_failing_gives_template(client, team):
    use_llms(llm1=Boom(responses=[]), llm2=Boom(responses=[]), llm3=Boom(responses=[]))
    try:
        b = client.post("/pulse", json={**team, "step": 13}).json()
    finally:
        app.dependency_overrides.clear()
    assert b["source"] == "template" and b["provider"] is None


def test_chat_falls_back_to_next_llm(client, team):
    use_llms(llm1=Boom(responses=[]), llm2=ToolFake(responses=[AIMessage(content="Gemini answer.")]))
    try:
        r = client.post("/chat", json={**team, "step": 5, "messages": [{"role": "user", "content": "hi"}]}).json()
    finally:
        app.dependency_overrides.clear()
    assert r == {"reply": "Gemini answer.", "provider": "gemini", "degraded": False}