from app.ai.agents.tools import build_tools
from app.core.config import get_settings
from app.domain.scoring import sample_team
from app.repositories.match_repo import MatchRepository


def _tools(step=30):
    match = MatchRepository(get_settings().data_dir).get("sample_match")
    xi, cap, vc = sample_team(match.balls)
    return {t.name: t for t in build_tools(match, step, xi, cap, vc)}, xi, cap, vc


def test_all_players_lists_whole_xi_in_one_call():
    tools, xi, *_ = _tools()
    out = tools["get_all_players"].invoke({})
    assert all(p in out for p in xi) and len(out.splitlines()) == 11


def test_best_captain_ranks_and_is_consistent():
    tools, xi, cap, vc = _tools()
    lines = tools["best_captain"].invoke({}).splitlines()
    assert lines[0].startswith(f"Current captain {cap}")
    totals = [float(l.split("->")[1].split()[0]) for l in lines[1:]]
    assert totals == sorted(totals, reverse=True) and len(totals) == 5


def test_all_tools_registered():
    tools, *_ = _tools()
    assert {"get_all_players", "best_captain", "what_if", "get_team_points"} <= set(tools)
