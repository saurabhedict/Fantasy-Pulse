"""Generate a synthetic T20 match in Cricsheet JSON format (for offline demo/testing).

For the real demo, download a match from https://cricsheet.org/downloads/ (JSON) and drop it in data/.
"""
import json
import os
import random

A = "Lions XI"
B = "Tigers XI"
NAMES = {
    A: ["A Verma", "K Nair", "S Menon", "R Chauhan", "D Patil", "M Kulkarni",
        "T Reddy", "P Joshi", "N Bhatt", "V Rao", "J Singh"],
    B: ["H Malik", "Y Desai", "C Gupta", "B Pillai", "G Thakur", "L Mishra",
        "F Qureshi", "I Banerjee", "O Sethi", "E Yadav", "U Kapoor"],
}
OUT = ["0", "1", "2", "3", "4", "6", "W", "wd", "nb"]
KINDS = ["bowled", "caught", "lbw", "caught and bowled", "stumped", "run out"]
KIND_W = [25, 45, 12, 5, 5, 8]


def weights(ov):
    if ov < 6:
        return [30, 26, 6, 1, 16, 6, 5, 3, 1]
    if ov >= 16:
        return [26, 26, 8, 1, 13, 11, 7, 3, 1]
    return [32, 30, 8, 1, 11, 6, 5, 3, 1]


def innings(bat, bowl, rng, target=None):
    batters, bowlers, keeper = NAMES[bat], NAMES[bowl], NAMES[bowl][0]
    striker, non, nxt = batters[0], batters[1], 2
    total = wk = 0
    overs, done = [], False
    for ov in range(20):
        bowler = bowlers[6 + ov % 5]
        dels, legal = [], 0
        while legal < 6 and not done:
            o = rng.choices(OUT, weights(ov))[0]
            d = {"batter": striker, "bowler": bowler, "non_striker": non,
                 "runs": {"batter": 0, "extras": 0, "total": 0}}
            if o == "wd":
                d["runs"].update(extras=1, total=1)
                d["extras"] = {"wides": 1}
            elif o == "nb":
                r = rng.choice([0, 1, 2, 4, 6])
                d["runs"].update(batter=r, extras=1, total=r + 1)
                d["extras"] = {"noballs": 1}
            else:
                legal += 1
                if o == "W":
                    kind = rng.choices(KINDS, KIND_W)[0]
                    fielders = []
                    if kind == "caught":
                        fielders = [{"name": rng.choice([p for p in bowlers if p != bowler])}]
                    elif kind == "caught and bowled":
                        fielders = [{"name": bowler}]
                    elif kind == "stumped":
                        fielders = [{"name": keeper}]
                    elif kind == "run out":
                        fielders = [{"name": rng.choice(bowlers)}]
                    d["wickets"] = [{"player_out": striker, "kind": kind, "fielders": fielders}]
                    wk += 1
                else:
                    r = int(o)
                    d["runs"].update(batter=r, total=r)
                    total += r
                    if r % 2 == 1:
                        striker, non = non, striker
            if o in ("wd", "nb"):
                total += d["runs"]["total"]
                if o == "nb" and d["runs"]["batter"] % 2 == 1:
                    striker, non = non, striker
            dels.append(d)
            if o == "W":
                if nxt < 11 and wk < 10:
                    striker, nxt = batters[nxt], nxt + 1
                else:
                    done = True
            if target and total >= target:
                done = True
        if dels:
            overs.append({"over": ov, "deliveries": dels})
        if done:
            break
        striker, non = non, striker
    return {"team": bat, "overs": overs}, total, wk


def make(seed):
    rng = random.Random(seed)
    i1, t1, _ = innings(A, B, rng)
    i2, t2, w2 = innings(B, A, rng, target=t1 + 1)
    return i1, i2, t1, t2, w2


if __name__ == "__main__":
    for seed in range(1, 2000):
        i1, i2, t1, t2, w2 = make(seed)
        close = (t2 > t1 and len(i2["overs"]) >= 19) or (0 < t1 - t2 <= 12)
        if 160 <= t1 <= 190 and close:
            break
    outcome = f"{B} won by {10 - w2} wickets" if t2 > t1 else f"{A} won by {t1 - t2} runs"
    info = {"teams": [A, B], "players": NAMES, "dates": ["2026-01-01"], "overs": 20,
            "match_type": "T20", "event": {"name": "Synthetic demo match"}, "outcome": outcome}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "app", "data", "matches", "sample_match.json"), "w") as f:
        json.dump({"info": info, "innings": [i1, i2]}, f)
    print(f"seed={seed}  {A} {t1}  {B} {t2}/{w2}  -> {outcome}")
