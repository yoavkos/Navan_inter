from urllib.parse import urlparse

import anthropic
from pydantic import BaseModel

from ai_fact_extractor import MODEL

SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 3}

SEARCH_PROMPT = """Find independent sources about this company: {company_name} ({domain}).
Look for: number of employees, offices and countries, funding rounds, parent company, industry.
Prefer news articles, company registries and Wikipedia.
Do NOT return pages from {domain} itself.
Make sure each source is about this company, not another company with a similar name.
Return up to 5 URLs."""


class SourceList(BaseModel):
    """URLs of external sources about the company."""
    urls: list[str]


def find_sources(company_name: str, domain: str) -> list[str]:
    """Let the LLM search the web, then keep only real, external URLs it actually found."""
    response = anthropic.Anthropic().messages.parse(
        model=MODEL,
        max_tokens=16000,
        tools=[SEARCH_TOOL],
        messages=[{"role": "user", "content": SEARCH_PROMPT.format(company_name=company_name, domain=domain)}],
        output_format=SourceList,
    )
    found = {result.url for block in response.content
             if block.type == "web_search_tool_result" and isinstance(block.content, list)
             for result in block.content}
    return [url for url in response.parsed_output.urls
            if url in found and domain not in urlparse(url).netloc]


if __name__ == "__main__":
    for url in find_sources("Greyparrot", "greyparrot.ai"):
        print(url)
