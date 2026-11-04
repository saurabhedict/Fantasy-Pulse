from app.core.errors import InvalidTeam, StepOutOfRange
from app.domain.models import Match


def validate_team(match: Match, xi: list, captain: str, vc: str, step: int | None = None) -> None:
    unknown = [p for p in xi if p not in match.players]
    if unknown:
        raise InvalidTeam(f"Players not in this match: {', '.join(unknown)}")
    if step is not None and not 1 <= step <= len(match.timeline):
        raise StepOutOfRange(f"step must be between 1 and {len(match.timeline)}")
