"""Where each fan player stands right now, plus fuzzy player-name matching."""
import difflib
from collections import defaultdict

from app.domain.scoring import BOWLER_WICKETS


def player_status(all_balls, so_far, tl, step, xi, max_overs=20):
    cur = tl[step - 1][0] if step > 0 else 1
    quota = max(1, max_overs // 5)
    bat_inn, bowl_inn = {}, {}
    for b in all_balls:
        bat_inn.setdefault(b["batter"], b["inning"])
        if b.get("non_striker"):
            bat_inn.setdefault(b["non_striker"], b["inning"])
        bowl_inn.setdefault(b["bowler"], b["inning"])
    runs, faced, out = defaultdict(int), set(), {}
    wkts, overs = defaultdict(int), defaultdict(set)
    for b in so_far:
        faced.add(b["batter"])
        if b.get("non_striker"):
            faced.add(b["non_striker"])
        runs[b["batter"]] += b["bat_runs"]
        overs[b["bowler"]].add((b["inning"], b["over"]))
        if b["wicket"]:
            if b["kind"] in BOWLER_WICKETS:
                wkts[b["bowler"]] += 1
            out[b["out_player"]] = b["kind"]
    status = {}
    for p in xi:
        if p in out:
            bat = f"out ({out[p]}) on {runs[p]}"
        elif p in faced:
            bat = f"not out, {runs[p]} runs" if bat_inn.get(p) == cur else f"finished not out on {runs[p]}"
        elif p in bat_inn:
            bat = "yet to bat" if bat_inn[p] >= cur else "did not bat"
        else:
            bat = "did not bat"
        left = None
        if p in bowl_inn:
            left = 0 if bowl_inn[p] < cur else max(0, quota - len(overs[p]))
        status[p] = {"batting": bat, "runs": runs[p], "wickets": wkts[p], "overs_left": left}
    return status


def resolve_player(name, candidates):
    """Match 'kohli' / 'V Kohli' / 'Kohly' to an exact roster name, or None."""
    if not name:
        return None
    low = {c.lower(): c for c in candidates}
    n = name.strip().lower()
    if n in low:
        return low[n]
    hits = [c for c in candidates if n in c.lower()]
    if hits:
        return hits[0]
    m = difflib.get_close_matches(n, list(low), n=1, cutoff=0.6)
    return low[m[0]] if m else None
