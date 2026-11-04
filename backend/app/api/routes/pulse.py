from fastapi import APIRouter, Depends

from app.api.deps import get_pulse_service
from app.schemas.pulse import PulseRequest, PulseResponse
from app.services.pulse_service import PulseService

router = APIRouter(prefix="/pulse", tags=["pulse"])


@router.post("", response_model=PulseResponse)
def pulse(req: PulseRequest, svc: PulseService = Depends(get_pulse_service)):
    """Fan's fantasy points, the change this over, and a plain-language explanation."""
    return svc.run(req)
