from dataclasses import dataclass


@dataclass(frozen=True)
class Match:
    id: str
    label: str
    teams: list
    players: list
    balls: list        # one dict per delivery, in match order
    timeline: list     # [(inning, over), ...]; step k = after the first k overs
    max_overs: int
