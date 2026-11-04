from app.domain.scoring import sample_team
from app.domain.timeline import over_label
from app.repositories.match_repo import MatchRepository
from app.schemas.match import MatchDetail, MatchSummary, SampleTeam


class MatchService:
    def __init__(self, repo: MatchRepository):
        self.repo = repo

    def list(self) -> list[MatchSummary]:
        return [MatchSummary(id=m.id, label=m.label, teams=m.teams) for m in self.repo.list_matches()]

    def detail(self, match_id: str) -> MatchDetail:
        m = self.repo.get(match_id)
        return MatchDetail(id=m.id, label=m.label, teams=m.teams, players=m.players,
                           total_steps=len(m.timeline), max_overs=m.max_overs,
                           step_labels=[over_label(m.timeline, s) for s in range(1, len(m.timeline) + 1)])

    def sample_team(self, match_id: str) -> SampleTeam:
        xi, captain, vc = sample_team(self.repo.get(match_id).balls)
        return SampleTeam(xi=xi, captain=captain, vc=vc)
