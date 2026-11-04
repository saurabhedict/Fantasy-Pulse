"""Fantasy Pulse - Streamlit UI (talks to the FastAPI backend)."""
import os
import time

import streamlit as st

from api_client import ApiError, PulseAPI

st.set_page_config(page_title="Fantasy Pulse", page_icon="🏏", layout="centered")


def api_url() -> str:
    try:
        return st.secrets["API_URL"]
    except Exception:
        return os.environ.get("API_URL", "http://localhost:8000")


URL = api_url()
API = PulseAPI(URL)


@st.cache_data(ttl=300, show_spinner="Loading matches...")
def get_matches(url):
    return PulseAPI(url).matches()


@st.cache_data(ttl=300)
def get_match(url, match_id):
    return PulseAPI(url).match(match_id)


for k, v in dict(started=False, step=1, playing=False, advance=False,
                 cache={}, messages=[], cfg=None, notice=None).items():
    st.session_state.setdefault(k, v)


# ---------- callbacks ----------
def use_sample(match_id):
    try:
        t = API.sample_team(match_id)
        st.session_state.xi_sel, st.session_state.cap_sel, st.session_state.vc_sel = t["xi"], t["captain"], t["vc"]
    except ApiError as e:
        st.session_state.notice = str(e)


def toggle_play(n):
    if not st.session_state.playing and st.session_state.step >= n:
        st.session_state.step = 1
    st.session_state.playing = not st.session_state.playing


def pause():
    st.session_state.playing = False


def reset():
    st.session_state.update(started=False, playing=False, step=1, messages=[], cache={})


def fail(e: Exception):
    st.error(f"{e}")
    st.stop()


# ---------- views ----------
def setup_view():
    try:
        matches = get_matches(URL)
    except ApiError as e:
        st.error(f"{e}")
        st.caption("Start the backend first: `cd backend && uvicorn app.main:app --reload`")
        st.stop()
    if not matches:
        st.warning("The API has no matches. Add a Cricsheet JSON to backend/app/data/matches/.")
        st.stop()

    labels = {m["id"]: m["label"] for m in matches}
    match_id = st.selectbox("Match", list(labels), format_func=labels.get, key="match_id")
    try:
        detail = get_match(URL, match_id)
    except ApiError as e:
        fail(e)

    if "xi_sel" in st.session_state:
        st.session_state.xi_sel = [p for p in st.session_state.xi_sel if p in detail["players"]]
    st.multiselect("Your XI (pick 11)", detail["players"], key="xi_sel", max_selections=11)
    xi = st.session_state.get("xi_sel", [])
    for key in ("cap_sel", "vc_sel"):
        if st.session_state.get(key) not in xi:
            st.session_state.pop(key, None)
    c1, c2 = st.columns(2)
    cap = c1.selectbox("Captain (2x)", xi, key="cap_sel")
    vc = c2.selectbox("Vice-captain (1.5x)", xi, key="vc_sel")

    if st.session_state.notice:
        st.error(st.session_state.notice)
        st.session_state.notice = None

    b1, b2 = st.columns(2)
    b1.button("Use sample team", on_click=use_sample, args=(match_id,), use_container_width=True)
    if b2.button("Start watching", type="primary", use_container_width=True):
        if len(xi) != 11:
            st.warning("Pick exactly 11 players (or use the sample team).")
        elif cap is None or vc is None or cap == vc:
            st.warning("Pick two different players as captain and vice-captain.")
        else:
            st.session_state.update(started=True, step=1, playing=False, messages=[], cache={},
                                    cfg={"match_id": match_id, "xi": xi, "captain": cap, "vc": vc})
            st.rerun()


def main_view():
    cfg = st.session_state.cfg
    try:
        detail = get_match(URL, cfg["match_id"])
    except ApiError as e:
        fail(e)
    n = detail["total_steps"]
    team = {"match_id": cfg["match_id"], "xi": cfg["xi"], "captain": cfg["captain"], "vc": cfg["vc"]}

    if st.session_state.advance:
        st.session_state.advance = False
        st.session_state.step = min(st.session_state.step + 1, n)

    top = st.container()
    st.slider("Match progress (overs, both innings)", 1, n, key="step", on_change=pause)
    step = st.session_state.step
    st.caption(detail["step_labels"][step - 1])
    st.button("⏸ Pause" if st.session_state.playing else "▶ Play", on_click=toggle_play, args=(n,))

    key = (cfg["match_id"], tuple(cfg["xi"]), cfg["captain"], cfg["vc"], step)
    if key not in st.session_state.cache:
        try:
            with st.spinner("Pulse is thinking..."):
                st.session_state.cache[key] = API.pulse({**team, "step": step})
        except ApiError as e:
            st.session_state.playing = False
            fail(e)
    out = st.session_state.cache[key]
    sb = out["scoreboard"]

    with top:
        line = f"**{sb['team']}** {sb['score']} ({sb['overs']} ov)"
        if sb["inning"] == 2:
            line += f"  ·  target {sb['target']}, need {max(sb['need'], 0)} from {sb['balls_left']} balls"
            if sb["required_rate"]:
                line += f" (RRR {sb['required_rate']})"
        st.markdown(line)
        st.metric("Your fantasy points", f"{out['fan_total']:.1f}", delta=f"{out['fan_delta']:+.1f} this over")
        st.info(f"**Pulse says:** {out['explanation']}")
        if out["source"] == "template":
            st.caption("Template explanation. Configure an LLM key on the backend for AI explanations.")
        elif out.get("provider"):
            st.caption(f"Explained by {out['provider']}")

    st.line_chart({"Your points": out["history"]})
    st.caption("Simplified fantasy scoring: runs, 4s/6s, 30/50/100 bonuses, wickets, fielding, ducks; C 2x, VC 1.5x.")

    st.subheader("💬 Ask Pulse")
    for m in st.session_state.messages:
        st.chat_message(m["role"]).write(m["content"])
    q = st.chat_input("e.g. Who still has overs left in my team?")
    if q:
        st.session_state.messages.append({"role": "user", "content": q})
        st.chat_message("user").write(q)
        try:
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    reply = API.chat({**team, "step": step, "messages": st.session_state.messages})["reply"]
                st.write(reply)
        except ApiError as e:
            reply = f"Chat is unavailable: {e}"
            st.chat_message("assistant").write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

    st.button("↩ New team", on_click=reset)

    if st.session_state.playing:
        if step < n:
            time.sleep(1.5)
            st.session_state.advance = True
            st.rerun()
        else:
            st.session_state.playing = False


st.title("🏏 Fantasy Pulse")
st.caption("Watch what's happening to *your* fantasy team, and why.")
if st.session_state.started and st.session_state.cfg:
    main_view()
else:
    setup_view()
