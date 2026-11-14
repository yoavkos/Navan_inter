from datetime import date
from typing import Literal

import anthropic
import pandas as pd
from pydantic import BaseModel

from ai_fact_extractor import MODEL
from decision_rules import site
from evidence import load_verified_facts

JUDGE_PROMPT = """You review a new business-travel customer and recommend whether its support tier fits.
Today is {today}.

Tiers:
- Tier 1: $500K+ annual travel spend (GBV) - dedicated account executive and account manager.
- Tier 2: $100K-$500K GBV, or 150+ employees - an account executive drives adoption.
- Tier 3: everything else - self-serve, product-led.

Signup data (entered by the customer or estimated):
- Company: {company_name} ({domain})
- Declared annual GBV: ${gbv:,}
- Estimated employees: {employees}
- Current tier: Tier {tier}

Verified research facts (each checked against its source, with its date when known):
{facts}

Weigh both numbers and softer signals (industry and how much it travels, international presence,
growth and its timing, parent company, contradictions between sources). Use only the data above.

Recommend one level:
- green: the current tier fits the evidence.
- yellow: a minor concern worth a glance (weak or general doubts), but no specific evidence the tier is wrong.
- orange: a strong concern a person should review soon - specific evidence the tier may not fit,
  or dated evidence of unusually fast or large change (for example rapid funding growth or fast hiring).
- red: strong evidence from 2+ independent sources that the company belongs in a HIGHER tier.
  Never use red for a lower tier - use orange.

First write a short reason (2-3 sentences) naming the facts and dates you relied on, then the level."""


class Judgment(BaseModel):
    """The AI reviewer's independent recommendation - four levels, used to settle disagreements."""
    reason: str
    color: Literal["green", "yellow", "orange", "red"]


def format_facts(facts: list[dict]) -> str:
    """One line per verified fact - 'field: value (source site, date)'."""
    lines = [f"- {f['field']}: {f['value']} ({site(f['source_url'])}"
             + (f", {f['source_date']})" if f["source_date"] else ")") for f in facts]
    return "\n".join(lines) or "- (none found)"


def ai_judgment(row) -> Judgment:
    """Ask the LLM for an independent recommendation from signup data and all verified facts."""
    prompt = JUDGE_PROMPT.format(
        today=date.today().isoformat(),
        company_name=row["company_name"], domain=row["company_domain"], gbv=row["gbv"],
        employees=row["employees"] if pd.notna(row["employees"]) else "unknown",
        tier=row["current_tier"], facts=format_facts(load_verified_facts(row["company_domain"])),
    )
    response = anthropic.Anthropic().messages.parse(
        model=MODEL,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
        output_format=Judgment,
    )
    return response.parsed_output
