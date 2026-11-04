"""Template explanation used whenever the LLM is missing or fails. The API never 500s because of the LLM."""


def template_explanation(ctx: dict) -> str:
    d = ctx["fan_delta"]
    verb = "gained" if d >= 0 else "lost"
    text = f"You {verb} {abs(d):.1f} points this over (total {ctx['fan_total']:.1f})."
    if ctx["biggest_movers"]:
        m = ctx["biggest_movers"][0]
        text += f" Biggest mover: {m['player']} ({m['change']:+.1f}, {m['role']})."
    c = ctx["captain_status"]
    text += f" Your captain {c['name']}: {c['batting']}."
    return text
