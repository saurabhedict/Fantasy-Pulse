"""Match timeline helpers. Step k = state after the first k completed overs (both innings)."""
RETIRED = {"retired hurt"}


def build_timeline(balls):
    seen, tl = set(), []
    for b in balls:
        key = (b["inning"], b["over"])
        if key not in seen:
            seen.add(key)
            tl.append(key)
    return tl


def balls_upto(balls, tl, step):
    done = set(tl[:max(step, 0)])
    return [b for b in balls if (b["inning"], b["over"]) in done]


def over_balls(balls, tl, step):
    if step < 1:
        return []
    inn, ov = tl[step - 1]
    return [b for b in balls if b["inning"] == inn and b["over"] == ov]


def over_label(tl, step):
    inn, ov = tl[step - 1]
    return f"Innings {inn}, over {ov + 1}"


def scoreboard(balls, tl, step, max_overs=20):
    """Score of the innings in progress at this step, plus chase info in innings 2."""
    inn = tl[step - 1][0]
    mine = [b for b in balls_upto(balls, tl, step) if b["inning"] == inn]
    runs = sum(b["total"] for b in mine)
    wkts = sum(1 for b in mine if b["wicket"] and b["kind"] not in RETIRED)
    legal = sum(1 for b in mine if b["legal"])
    sb = {"inning": inn, "team": mine[0]["team"], "score": f"{runs}/{wkts}",
          "overs": f"{legal // 6}.{legal % 6}", "runs": runs, "wickets": wkts}
    if inn == 2:
        target = sum(b["total"] for b in balls if b["inning"] == 1) + 1
        balls_left = max_overs * 6 - legal
        need = target - runs
        sb.update(target=target, need=need, balls_left=balls_left,
                  required_rate=round(need * 6 / balls_left, 2) if balls_left > 0 and need > 0 else 0.0)
    return sb
