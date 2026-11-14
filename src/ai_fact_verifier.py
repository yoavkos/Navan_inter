import anthropic
from pydantic import BaseModel

from ai_fact_extractor import FIELD_DEFINITIONS, MODEL, Fact

SOURCE_CONTEXT = {
    "website": "The quote comes from the company's own website ({domain}).\n"
               "Statements without a company name, or with a name variant (e.g. \"Dalkia UK\"), refer to this company.",
    "search": "The quote comes from an external page that was checked and is about this company ({domain}).\n"
              "Statements without a company name refer to this company, unless the quote names a different company.",
}

VERIFY_PROMPT = """You check whether a quote supports a fact about a company.

Company: {company_name}
{source_context}

""" + FIELD_DEFINITIONS + """

Field: {field}
Claimed value: {value}
Quote: "{quote}"

Answer supported=true only if the quote directly states this value about the company itself
(not about its customers, partners, products or market).
First give a one-sentence reason, then the answer."""


class Verdict(BaseModel):
    """The verifier's answer for one fact."""
    reason: str
    supported: bool


def llm_supports(fact: Fact, company_name: str, domain: str, source: str = "website") -> Verdict:
    """Ask the LLM whether the quote really supports the fact's value - source is "website" or "search"."""
    source_context = SOURCE_CONTEXT[source].format(domain=domain)
    prompt = VERIFY_PROMPT.format(company_name=company_name, source_context=source_context, **fact.model_dump())
    response = anthropic.Anthropic().messages.parse(
        model=MODEL,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
        output_format=Verdict,
    )
    return response.parsed_output


if __name__ == "__main__":
    real = Fact(field="employees", value="over 50 people", source_date=None,
                quote="We're a team of over 50 people from 23 nationalities",
                source_url="https://www.greyparrot.ai/about-us")
    customers = Fact(field="countries", value="20+ countries", source_date=None,
                     quote="80+ materials recovery facilities across 20+ countries",
                     source_url="https://greyparrot.ai")
    for fact in [customers, real]:
        verdict = llm_supports(fact, "Greyparrot", "greyparrot.ai")
        print(f"{fact.value}: supported={verdict.supported} - {verdict.reason}")
