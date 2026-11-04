from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import TeamIn


class PulseRequest(TeamIn):
    step: int = Field(ge=1, description="Number of completed overs to show (1-based)")


class Scoreboard(BaseModel):
    inning: int
    team: str | None = None
    score: str
    overs: str
    runs: int
    wickets: int
    target: int | None = None
    need: int | None = None
    balls_left: int | None = None
    required_rate: float | None = None


class PulseResponse(BaseModel):
    match_id: str
    step: int
    total_steps: int
    moment: str
    scoreboard: Scoreboard
    fan_total: float
    fan_delta: float
    explanation: str
    source: Literal["ai", "template"]
    provider: str | None = None     # which LLM answered: groq / gemini / aion
    big_swing: bool
    key_events: list[dict]
    biggest_movers: list[dict]
    history: list[float]
