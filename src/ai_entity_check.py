import anthropic
from pydantic import BaseModel

from ai_fact_extractor import MODEL

MAX_PAGE_CHARS = 3000

ENTITY_PROMPT = """Is this web page mainly about the company {company_name} ({domain})?
Answer about_company=true only if the page is clearly about this specific company -
not another company with a similar name, and not a list of many companies.
First give a one-sentence reason, then the answer.

Page ({url}):
{text}"""


class PageVerdict(BaseModel):
    """Whether a web page is about the target company."""
    reason: str
    about_company: bool


def page_is_about(company_name: str, domain: str, url: str, text: str) -> PageVerdict:
    """Ask the LLM whether a page is about this company - reads only the start of the page."""
    prompt = ENTITY_PROMPT.format(company_name=company_name, domain=domain, url=url,
                                  text=text[:MAX_PAGE_CHARS])
    response = anthropic.Anthropic().messages.parse(
        model=MODEL,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
        output_format=PageVerdict,
    )
    return response.parsed_output
