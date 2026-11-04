"""Loads Cricsheet ball-by-ball JSON files into Match objects (cached in memory)."""
import json
import re
from pathlib import Path

from app.core.errors import MatchNotFound
from app.domain.models import Match
from app.domain.timeline import build_timeline

_ID_OK = re.compile(r"^[\w\-.]+$")


def parse_cricsheet(match_id: str, raw: dict) -> Match:
    info = raw.get("info", {})
    balls = []
    for inn_no, inn in enumerate(raw.get("innings", []), 1):
        if inn.get("super_over"):
            continue
        for ov in inn.get("overs", []):
            for b_no, d in enumerate(ov["deliveries"], 1):
                wk = d.get("wickets", [])
                w = wk[0] if wk else None
                extras = d.get("extras", {})
                balls.append({
                    "inning": inn_no, "team": inn.get("team"), "over": ov["over"], "ball": b_no,
                    "batter": d["batter"], "non_striker": d.get("non_striker"), "bowler": d["bowler"],
                    "bat_runs": d["runs"]["batter"], "extras": d["runs"]["extras"], "total": d["runs"]["total"],
                    "legal": not ("wides" in extras or "noballs" in extras),
                    "wicket": bool(w), "out_player": w["player_out"] if w else None,
                    "kind": w["kind"] if w else None,
                    "fielders": [f["name"] for f in w.get("fielders", []) if f.get("name")] if w else [],
                })
    names = set()
    for plist in (info.get("players") or {}).values():
        names.update(plist)
    if not names:
        for b in balls:
            names.update(x for x in (b["batter"], b["non_striker"], b["bowler"]) if x)
    teams = info.get("teams", [])
    event = (info.get("event") or {}).get("name", "match") if isinstance(info.get("event"), dict) else "match"
    label = f"{' vs '.join(teams)} ({event})" if teams else match_id
    return Match(id=match_id, label=label, teams=teams, players=sorted(names), balls=balls,
                 timeline=build_timeline(balls), max_overs=info.get("overs", 20))


class MatchRepository:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self._cache: dict[str, Match] = {}

    def list_ids(self) -> list[str]:
        return sorted(p.stem for p in self.data_dir.glob("*.json"))

    def get(self, match_id: str) -> Match:
        if match_id in self._cache:
            return self._cache[match_id]
        path = self.data_dir / f"{match_id}.json"
        if not _ID_OK.match(match_id) or ".." in match_id or not path.is_file():
            raise MatchNotFound(f"Match '{match_id}' not found")
        with open(path, encoding="utf-8") as f:
            match = parse_cricsheet(match_id, json.load(f))
        self._cache[match_id] = match
        return match

    def list_matches(self) -> list[Match]:
        return [self.get(i) for i in self.list_ids()]
