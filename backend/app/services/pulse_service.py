from app.ai.graphs.pulse_graph import run_pulse
from app.core.config import Settings
from app.domain.scoring import history
from app.repositories.match_repo import MatchRepository
from app.schemas.pulse import PulseRequest, PulseResponse
from app.services.validation import validate_team


class PulseService:
    def __init__(self, repo: MatchRepository, llms, settings: Settings):
        self.repo, self.llms, self.settings = repo, llms, settings

    def run(self, req: PulseRequest) -> PulseResponse:
        match = self.repo.get(req.match_id)
        validate_team(match, req.xi, req.captain, req.vc, req.step)
        out = run_pulse(balls=match.balls, tl=match.timeline, step=req.step, xi=req.xi,
                        captain=req.captain, vc=req.vc, max_overs=match.max_overs,
                        llms=self.llms, threshold=self.settings.big_swing_threshold)
        ctx = out["ctx"]
        return PulseResponse(
            match_id=match.id, step=req.step, total_steps=len(match.timeline), moment=ctx["moment"],
            scoreboard=ctx["match"], fan_total=ctx["fan_total"], fan_delta=ctx["fan_delta"],
            explanation=out["explanation"], source=out["source"], provider=out.get("provider"),
            big_swing=bool(ctx.get("big_swing")), key_events=ctx["key_events"],
            biggest_movers=ctx["biggest_movers"],
            history=history(match.balls, match.timeline, req.step, req.xi, req.captain, req.vc))