import re

import anthropic
from pydantic import BaseModel

from ai_fact_extractor import MODEL

HEADLINES = {"red": "Consider a higher tier", "yellow": "Review needed", "green": "Tier fits"}
ICONS = {"green": "🟢", "yellow": "🟡", "orange": "🟠", "red": "🔴"}

NOTE_PROMPT = """Write a short note for a sales rep about {company_name} (current Tier {tier}).
The recommendation is already decided: {headline}. Do not change it - explain it.

Rules reasons:
{rules_reasons}

AI reviewer reason:
{ai_reason}

Verified facts:
{facts}

Write at most 2 sentences and 40 words, plain English, for a busy sales rep:
- Do not repeat the recommendation - the rep already sees it as the headline. Start with WHY.
- Lead with the single most important fact, then at most one supporting fact.
- Give numbers with their source site in brackets, e.g. "206 employees (tracxn.com)".
- Use numbers exactly as they appear above. Never add numbers that are not above.
- No internal terms (flags, rules, signup check, AI reviewer, unrecognized locations).
- End with what to check, if anything, in a few words.
- {disagreement}"""


class Note(BaseModel):
    """The note text shown to the sales rep."""
    text: str


def numbers_in(text: str) -> set[str]:
    """All numbers in a text, without commas - '$1,000' -> '1000'."""
    return {n.replace(",", "") for n in re.findall(r"\d[\d,.]*\d|\d", text)}


def write_note(company_name: str, tier: int, final: str, priority: str, agreement: bool,
               rules_reasons: list[str], ai_reason: str, facts_text: str) -> dict:
    """Ask the LLM for a short note, then check in code that every number in it comes from the input."""
    headline = HEADLINES[final] + (" - high priority" if priority == "high" else "")
    reasons = "\n".join(f"- {r}" for r in rules_reasons) or "- (none)"
    disagreement = ("The two reviews disagreed - say in a few words that the evidence is mixed."
                    if not agreement else "Both reviews agree - do not mention any disagreement.")
    prompt = NOTE_PROMPT.format(company_name=company_name, tier=tier, headline=headline, disagreement=disagreement,
                                rules_reasons=reasons, ai_reason=ai_reason, facts=facts_text)
    response = anthropic.Anthropic().messages.parse(
        model=MODEL,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
        output_format=Note,
    )
    text = response.parsed_output.text
    unsupported = numbers_in(text) - numbers_in(prompt)
    return {
        "headline": f"{ICONS[final]} {headline}",
        "text": text,
        "numbers_checked": not unsupported,
        "unsupported_numbers": sorted(unsupported),
    }
