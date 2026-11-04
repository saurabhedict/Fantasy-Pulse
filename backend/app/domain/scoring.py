"""Fantasy points engine. SIMPLIFIED scoring - say so in any UI/note."""
from collections import defaultdict

from app.domain.timeline import balls_upto

BOWLER_WICKETS = {"bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"}
RUN_MILESTONES = ((30, 4), (50, 8), (100, 16))   # (runs reached, bonus)
WICKET_POINTS = 25
FIELDER_POINTS = 8


def player_points(balls):
    pts, runs = defaultdict(float), defaultdict(int)
    for b in balls:
        bat, r = b["batter"], b["bat_runs"]
        before = runs[bat]
        runs[bat] += r
        pts[bat] += r
        if r == 4:
            pts[bat] += 1
        if r == 6:
            pts[bat] += 2
        for threshold, bonus in RUN_MILESTONES:
            if before < threshold <= runs[bat]:
                pts[bat] += bonus
        if b["wicket"]:
            kind = b["kind"]
            if kind in BOWLER_WICKETS:
                pts[b["bowler"]] += WICKET_POINTS
            for f in b["fielders"]:
                if f != b["bowler"]:
                    pts[f] += FIELDER_POINTS
            out = b["out_player"]
            if out and kind != "retired hurt" and runs[out] == 0:
                pts[out] -= 2   # duck
    return pts


def multiplier(player, captain, vc):
    return 2.0 if player == captain else 1.5 if player == vc else 1.0


def team_points(pts, xi, captain, vc):
    return sum(pts.get(p, 0.0) * multiplier(p, captain, vc) for p in xi)


def breakdown(pts_now, pts_prev, xi, captain, vc):
    """Per-player change in the fan's points, biggest movers first."""
    rows = []
    for p in xi:
        d = (pts_now.get(p, 0.0) - pts_prev.get(p, 0.0)) * multiplier(p, captain, vc)
        if d:
            rows.append({"player": p, "change": round(d, 1)})
    return sorted(rows, key=lambda r: abs(r["change"]), reverse=True)


def history(balls, tl, upto_step, xi, captain, vc):
    """Fan's total after each over (for the chart)."""
    return [round(team_points(player_points(balls_upto(balls, tl, s)), xi, captain, vc), 1)
            for s in range(1, upto_step + 1)]


def sample_team(balls):
    """Demo team: the 11 highest scorers of the match; captain/VC = top two."""
    pts = player_points(balls)
    ranked = [p for p, _ in sorted(pts.items(), key=lambda kv: kv[1], reverse=True)][:11]
    return ranked, ranked[0], ranked[1]
