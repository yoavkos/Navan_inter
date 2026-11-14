import json
import sys
from pathlib import Path

from ai_entity_check import page_is_about
from ai_fact_extractor import extract_facts
from ai_web_search import find_sources
from load_data import load_set
from website_agent import FACTS_DIR, check_facts
from website_scraper import extract_text, fetch_html

SEARCH_PAGES_DIR = Path(__file__).parent.parent / "data" / "search_pages"
MIN_TEXT_LENGTH = 200


def collect_sources(company_name: str, domain: str) -> dict[str, str]:
    """Find external sources and download their text - skips pages that fail or are nearly empty."""
    pages = {}
    for url in find_sources(company_name, domain):
        try:
            text = extract_text(fetch_html(url))
        except Exception as error:
            print(f"  skipped {url} ({error})")
            continue
        if len(text) >= MIN_TEXT_LENGTH:
            pages[url] = text
    return pages


def keep_relevant_pages(pages: dict[str, str], company_name: str, domain: str) -> dict[str, str]:
    """Keep only pages that are about this company - print why others were dropped."""
    relevant = {}
    for url, text in pages.items():
        verdict = page_is_about(company_name, domain, url, text)
        if verdict.about_company:
            relevant[url] = text
        else:
            print(f"  dropped {url} ({verdict.reason})")
    return relevant


if __name__ == "__main__":
    out_dir = FACTS_DIR / "search"
    out_dir.mkdir(parents=True, exist_ok=True)
    SEARCH_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    set_name = sys.argv[1] if len(sys.argv) > 1 else "dev"
    for _, company in load_set(set_name).iterrows():
        name, domain = company["company_name"], company["company_domain"]
        print(name)
        saved = SEARCH_PAGES_DIR / f"{domain}.json"
        pages = json.loads(saved.read_text(encoding="utf-8")) if saved.exists() else collect_sources(name, domain)
        saved.write_text(json.dumps(pages, indent=2), encoding="utf-8")
        pages = keep_relevant_pages(pages, name, domain)
        if not pages:
            print("  no usable external pages")
            continue
        facts = extract_facts(name, domain, pages, "external web pages (news, company databases)")
        results = check_facts(facts, pages, name, domain, source="search")
        (out_dir / f"{domain}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        verified = sum(r["status"] == "verified" for r in results)
        print(f"  {len(pages)} pages, {verified} verified, {len(results) - verified} rejected")
