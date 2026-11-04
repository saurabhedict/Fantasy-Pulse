from fastapi import APIRouter, Depends

from app.api.deps import get_chat_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, svc: ChatService = Depends(get_chat_service)):
    """Ask Pulse a free-form question about the fan's team (LangGraph agent with tools)."""
    return svc.chat(req)
