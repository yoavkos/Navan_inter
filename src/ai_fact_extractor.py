import json
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel

MODEL = "claude-haiku-5-5"
PAGES_DIR = Path(__file__).parent.parent / "data" / "pages"

FIELD_DEFINITIONS = """Field definitions:
- employees: number of people working at the company itself.
- industry: what the company itself does or sells.
- countries: countries where the company itself has offices or staff.
  Countries of customers, users, installations or sales do NOT count.
- parent_company: a company that owns this company.
- funding: money the company itself raised (investment round, grant).
- hiring: the company itself is recruiting (open roles, "we're hiring")."""

PROMPT = """You extract facts about a company from {source_description}.

Company: {company_name} ({domain})

""" + FIELD_DEFINITIONS + """

Rules:
1. Use ONLY the text below. Do not use your own knowledge.
2. "quote" must be copied EXACTLY from the text, word for word.
3. If a field is not clearly stated, do not return it. Never guess.
4. If the text does not seem to be about this company, return no facts.
5. source_url: the URL in the "---" header above the quote.
6. source_date: only if a date appears in the text near the quote, else null.

Pages:
{pages}"""

FieldName = Literal["employees", "industry", "countries", "parent_company", "funding", "hiring"]


class Fact(BaseModel):
    """One fact about a company, with the exact quote that supports it."""
    field: FieldName
    value: str
    quote: str
    source_url: str
    source_date: str | None


class Facts(BaseModel):
    """All facts the model found - wraps the list because the schema root must be an object."""
    facts: list[Fact]


def load_pages(domain: str) -> dict[str, str]:
    """Load the saved pages of a company - {url: text}."""
    return json.loads((PAGES_DIR / f"{domain}.json").read_text(encoding="utf-8"))


def format_pages(pages: dict[str, str]) -> str:
    """Join saved pages into one text, each page under a '--- url ---' header."""
    return "\n\n".join(f"--- {url} ---\n{text}" for url, text in pages.items())


def extract_facts(company_name: str, domain: str, pages: dict[str, str], source_description: str) -> list[Fact]:
    """Ask the LLM to extract facts with exact quotes from the given pages."""
    prompt = PROMPT.format(company_name=company_name, domain=domain,
                           source_description=source_description, pages=format_pages(pages))
    response = anthropic.Anthropic().messages.parse(
        model=MODEL,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
        output_format=Facts,
    )
    print(f"  tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
    return response.parsed_output.facts


if __name__ == "__main__":
    for fact in extract_facts("Greyparrot", "greyparrot.ai", load_pages("greyparrot.ai"), "its own website text"):
        print(fact)
