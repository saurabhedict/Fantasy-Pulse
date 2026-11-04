"""Turn raw match state into a small JSON fact sheet (the only thing the LLM sees)."""
from app.domain.scoring import WICKET_POINTS, breakdown, multiplier, player_points, team_points
from app.domain.status import player_status
from app.domain.timeline import balls_upto, over_balls, over_label, scoreboard


def build_context(balls, tl, step, xi, captain, vc, max_overs=20):
    now, prev = balls_upto(balls, tl, step), balls_upto(balls, tl, step - 1)
    pn, pp = player_points(now), player_points(prev)
    total = team_points(pn, xi, captain, vc)
    delta = total - team_points(pp, xi, captain, vc)

    def role(p):
        return "captain" if p == captain else "vice-captain" if p == vc else "player"

    events = []
    for b in over_balls(balls, tl, step):
        people = [b["batter"], b["bowler"], b["out_player"], *b["fielders"]]
        involved = [{"player": p, "role": role(p)} for p in dict.fromkeys(people) if p in xi]
        if not involved:
            continue
        if b["wicket"]:
            events.append({"type": "wicket", "how": b["kind"], "out": b["out_player"],
                           "bowler": b["bowler"], "fielders": b["fielders"], "fan_players_involved": involved})
        elif b["bat_runs"] in (4, 6):
            events.append({"type": "six" if b["bat_runs"] == 6 else "four",
                           "batter": b["batter"], "bowler": b["bowler"], "fan_players_involved": involved})

    status = player_status(balls, now, tl, step, xi, max_overs)
    movers = [dict(m, role=role(m["player"])) for m in breakdown(pn, pp, xi, captain, vc)[:3]]
    bowlers_left = {p: s["overs_left"] for p, s in status.items() if s["overs_left"]}
    return {
        "moment": over_label(tl, step),
        "match": scoreboard(balls, tl, step, max_overs),
        "fan_total": round(total, 1),
        "fan_delta": round(delta, 1),
        "key_events": events[:6],
        "biggest_movers": movers,
        "captain_status": {"name": captain, **status[captain]},
        "vice_captain_status": {"name": vc, **status[vc]},
        "fan_bowlers_with_overs_left": bowlers_left,
        "points_per_wicket_for_fan": {p: WICKET_POINTS * multiplier(p, captain, vc) for p in bowlers_left},
    }
