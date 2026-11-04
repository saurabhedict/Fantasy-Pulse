from app.ai.agents.chat_agent import ask_agent, build_agent
from app.core.errors import LLMUnavailable
from app.repositories.match_repo import MatchRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.validation import validate_team


class ChatService:
    def __init__(self, repo: MatchRepository, llms):
        self.repo, self.llms = repo, llms

    def chat(self, req: ChatRequest) -> ChatResponse:
        match = self.repo.get(req.match_id)
        validate_team(match, req.xi, req.captain, req.vc, req.step)
        models = self.llms.ordered() if self.llms else []
        if not models:
            raise LLMUnavailable("Chat needs an LLM key on the server (GROQ_API_KEY, GOOGLE_API_KEY or AION_API_KEY).")
        history = [(m.role, m.content) for m in req.messages]
        last_reply = ""
        for name, model in models:          # try llm1, then llm2, then llm3
            agent = build_agent(model, match, req.step, req.xi, req.captain, req.vc)
            reply, ok = ask_agent(agent, history)
            if ok:
                return ChatResponse(reply=reply, provider=name, degraded=False)
            last_reply = reply
        return ChatResponse(reply=last_reply, provider=None, degraded=True)