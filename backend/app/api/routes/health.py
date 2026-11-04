from fastapi import APIRouter, Depends

from app.ai.llm import LLMs
from app.api.deps import get_llms

router = APIRouter(tags=["health"])


@router.get("/health")
def health(llms: LLMs = Depends(get_llms)):
    providers = [name for name, _ in llms.ordered()]
    return {"status": "ok", "llm_configured": bool(providers), "providers": providers}