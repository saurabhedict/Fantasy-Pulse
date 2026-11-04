from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.pulse import PulseRequest


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(PulseRequest):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def _last_is_user(self):
        if self.messages[-1].role != "user":
            raise ValueError("the last message must come from the user")
        return self


class ChatResponse(BaseModel):
    reply: str
    provider: str | None = None     # which LLM answered: groq / gemini / aion
    degraded: bool = False     # True if the agent failed and a fallback message was returned
