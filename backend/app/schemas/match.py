from pydantic import BaseModel


class MatchSummary(BaseModel):
    id: str
    label: str
    teams: list[str]


class MatchDetail(MatchSummary):
    players: list[str]
    total_steps: int
    max_overs: int
    step_labels: list[str]      # step_labels[k-1] describes step k


class SampleTeam(BaseModel):
    xi: list[str]
    captain: str
    vc: str
