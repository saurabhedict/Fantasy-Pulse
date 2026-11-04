from fastapi import APIRouter, Depends

from app.api.deps import get_match_service
from app.schemas.match import MatchDetail, MatchSummary, SampleTeam
from app.services.match_service import MatchService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchSummary])
def list_matches(svc: MatchService = Depends(get_match_service)):
    return svc.list()


@router.get("/{match_id}", response_model=MatchDetail)
def match_detail(match_id: str, svc: MatchService = Depends(get_match_service)):
    return svc.detail(match_id)


@router.get("/{match_id}/sample-team", response_model=SampleTeam)
def sample_team(match_id: str, svc: MatchService = Depends(get_match_service)):
    return svc.sample_team(match_id)
