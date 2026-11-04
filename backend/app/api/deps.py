"""Dependency wiring. Tests replace these with fakes via app.dependency_overrides."""
from functools import lru_cache

from fastapi import Depends

from app.ai.llm import LLMs, build_llms
from app.core.config import Settings, get_settings
from app.repositories.match_repo import MatchRepository
from app.services.chat_service import ChatService
from app.services.match_service import MatchService
from app.services.pulse_service import PulseService


@lru_cache
def get_repo() -> MatchRepository:
    return MatchRepository(get_settings().data_dir)


@lru_cache
def get_llms() -> LLMs:
    return build_llms(get_settings())


def get_match_service(repo: MatchRepository = Depends(get_repo)) -> MatchService:
    return MatchService(repo)


def get_pulse_service(repo: MatchRepository = Depends(get_repo), llms: LLMs = Depends(get_llms),
                      settings: Settings = Depends(get_settings)) -> PulseService:
    return PulseService(repo, llms, settings)


def get_chat_service(repo: MatchRepository = Depends(get_repo), llms: LLMs = Depends(get_llms)) -> ChatService:
    return ChatService(repo, llms)