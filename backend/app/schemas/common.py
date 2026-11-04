from pydantic import BaseModel, Field, model_validator


class TeamIn(BaseModel):
    match_id: str
    xi: list[str] = Field(min_length=11, max_length=11, description="Exactly 11 player names")
    captain: str
    vc: str

    @model_validator(mode="after")
    def _check(self):
        if len(set(self.xi)) != 11:
            raise ValueError("xi must contain 11 different players")
        if self.captain == self.vc:
            raise ValueError("captain and vc must be different players")
        if self.captain not in self.xi or self.vc not in self.xi:
            raise ValueError("captain and vc must be in the XI")
        return self
