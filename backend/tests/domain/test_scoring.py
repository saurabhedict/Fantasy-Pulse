from app.domain.scoring import player_points, team_points
from app.domain.status import resolve_player


def ball(batter="A", bowler="X", runs=0, wicket=False, kind=None, out=None, fielders=()):
    return {"inning": 1, "over": 0, "batter": batter, "non_striker": "B", "bowler": bowler,
            "bat_runs": runs, "wicket": wicket, "kind": kind, "out_player": out, "fielders": list(fielders)}


def test_runs_and_boundaries():
    assert player_points([ball(runs=1), ball(runs=4), ball(runs=6)])["A"] == 1 + (4 + 1) + (6 + 2)


def test_wicket_catch_duck():
    pts = player_points([ball(batter="D", wicket=True, kind="caught", out="D", fielders=["F"])])
    assert pts["X"] == 25 and pts["F"] == 8 and pts["D"] == -2


def test_run_out_gives_bowler_nothing():
    assert player_points([ball(wicket=True, kind="run out", out="A", fielders=["F"])]).get("X", 0) == 0


def test_milestone_and_multipliers():
    pts = player_points([ball(runs=6)] * 5)           # 30 runs: +4 milestone, +2 per six
    assert pts["A"] == 30 + 5 * 2 + 4
    assert team_points(pts, ["A", "B"], "A", "B") == pts["A"] * 2


def test_resolve_player():
    names = ["V Kohli", "H Pandya"]
    assert resolve_player("kohli", names) == "V Kohli"
    assert resolve_player("Pandia", names) == "H Pandya"
    assert resolve_player("zzz", names) is None
