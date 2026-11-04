"""Agent tools. Each one is a thin wrapper over domain code, so numbers are always exact."""
from langchain_core.tools import tool

from app.domain.models import Match
from app.domain.scoring import WICKET_POINTS, multiplier, player_points, team_points
from app.domain.status import player_status, resolve_player
from app.domain.timeline import balls_upto, scoreboard


def build_tools(match: Match, step: int, xi: list, captain: str, vc: str):
    so_far = balls_upto(match.balls, match.timeline, step)
    pts = player_points(so_far)

    def find(name):
        return resolve_player(name, xi) or resolve_player(name, match.players)

    @tool
    def get_match_state() -> str:
        """Current score, overs, and chase target/required rate of the match."""
        return str(scoreboard(match.balls, match.timeline, step, match.max_overs))

    @tool
    def get_team_points() -> str:
        """The fan's total fantasy points right now."""
        return f"Fan team total: {team_points(pts, xi, captain, vc):.1f}"

    @tool
    def get_player_breakdown(player: str) -> str:
        """Fantasy points one player has earned for the fan, multiplier included."""
        p = find(player)
        if p is None:
            return f"No player matching '{player}'."
        if p not in xi:
            return f"{p} is not in the fan's team."
        m = multiplier(p, captain, vc)
        return f"{p}: {pts.get(p, 0):.1f} base points x{m} = {pts.get(p, 0) * m:.1f}"

    @tool
    def get_remaining() -> str:
        """For each fan player: batting status and bowling overs left."""
        st = player_status(match.balls, so_far, match.timeline, step, xi, match.max_overs)
        return "\n".join(f"{p}: batting={s['batting']}; bowling overs left={s['overs_left']}"
                         for p, s in st.items())

    @tool
    def what_if(player: str, extra_runs: int = 0, extra_wickets: int = 0) -> str:
        """Fan's total if a player scores extra_runs more and/or takes extra_wickets more.
        Approximate: ignores boundary/milestone bonuses."""
        p = find(player)
        now = team_points(pts, xi, captain, vc)
        if p is None or p not in xi:
            return f"'{player}' is not in the fan's team, so no change. Total stays {now:.1f}."
        m = multiplier(p, captain, vc)
        new = now + (extra_runs + extra_wickets * WICKET_POINTS) * m
        return f"Now {now:.1f}. With +{extra_runs} runs, +{extra_wickets} wickets for {p} (x{m}): about {new:.1f}"

    @tool
    def get_all_players() -> str:
        """ONE call that lists every player in the fan's XI: base points, multiplier, fan points, batting status,
        bowling overs left. Use this to compare players or to answer questions about the whole team."""
        st = player_status(match.balls, so_far, match.timeline, step, xi, match.max_overs)
        rows = []
        for p in xi:
            m = multiplier(p, captain, vc)
            rows.append(f"{p}: base {pts.get(p, 0):.1f} x{m} = {pts.get(p, 0) * m:.1f}; "
                        f"batting={st[p]['batting']}; overs left={st[p]['overs_left']}")
        return "\n".join(rows)

    @tool
    def best_captain() -> str:
        """Hindsight comparison in ONE call: fan's total if each XI player had been captain (2x), best first.
        Note: in real fantasy apps the captain is locked once the match starts."""
        now = team_points(pts, xi, captain, vc)
        results = []
        for cand in xi:
            new_vc = captain if cand == vc else vc
            results.append((team_points(pts, xi, cand, new_vc), cand))
        results.sort(reverse=True)
        lines = [f"Current captain {captain}: total {now:.1f}"]
        lines += [f"{i}. {c} as captain -> {t:.1f} ({t - now:+.1f})" for i, (t, c) in enumerate(results[:5], 1)]
        return "\n".join(lines)

    return [get_match_state, get_team_points, get_player_breakdown, get_remaining,
            get_all_players, best_captain, what_if]
