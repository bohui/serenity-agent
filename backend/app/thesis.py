"""
Thesis writer. If ANTHROPIC_API_KEY is set, Claude writes the final
investment thesis from the gathered evidence (hybrid mode). Otherwise a
structured template assembles the same evidence deterministically.
"""
import os

SYSTEM = (
    "You are a supply-chain equity analyst using Serenity's (@aleabitoreddit) "
    "bottleneck framework: certain demand, constrained supply, low attention, "
    "value capture, near-term catalyst. Write a tight, skeptical thesis. "
    "Cite only the provided evidence. Include what would kill the thesis. "
    "This is research, not financial advice; say so in one closing line."
)


def _template_thesis(c: dict) -> str:
    f = c["factors"]
    seg, theme = c["segment_name"], c["theme_name"]
    lines = [
        f"**{c['ticker']} — {c['name']}** | {seg} ({theme})",
        "",
        f"**Chokepoint.** {c['why_critical']}",
        "",
        f"**Demand ({f['demand']['score']:.2f}).** " + " ".join(f["demand"]["evidence"][:2]),
        f"**Supply constraint ({f['supply']['score']:.2f}).** " + " ".join(f["supply"]["evidence"][:3]),
        f"**Attention gap ({f['attention']['score']:.2f}).** " + " ".join(f["attention"]["evidence"][:3]),
        f"**Value capture ({f['value_capture']['score']:.2f}).** " + " ".join(f["value_capture"]["evidence"][:2]),
        f"**Catalyst ({f['catalyst']['score']:.2f}).** " + " ".join(f["catalyst"]["evidence"][:2]),
        "",
        f"**Price context.** {c['momentum_note']}.",
        "**Kill criteria.** Capacity additions by competitors, demand-trend break, "
        "or the attention gap closing after a >100% re-rating.",
        "",
        "_Automated research output — not financial advice._",
    ]
    return "\n".join(lines)


def write_thesis(candidate: dict) -> tuple[str, str]:
    """Returns (thesis_markdown, engine) where engine is 'claude' or 'template'."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        try:
            import anthropic
            client = anthropic.Anthropic()
            evidence = {
                k: v for k, v in candidate.items()
                if k in ("ticker", "name", "segment_name", "theme_name", "why_critical",
                         "factors", "momentum_note", "metrics", "headlines")
            }
            msg = client.messages.create(
                model=os.environ.get("THESIS_MODEL", "claude-sonnet-4-5"),
                max_tokens=900,
                system=SYSTEM,
                messages=[{
                    "role": "user",
                    "content": "Write the thesis for this candidate. Evidence JSON:\n"
                               + str(evidence),
                }],
            )
            return msg.content[0].text, "claude"
        except Exception:
            pass
    return _template_thesis(candidate), "template"
