import json
import sys
from pathlib import Path

from ai_fact_extractor import PAGES_DIR, Fact, extract_facts, load_pages
from ai_fact_verifier import llm_supports
from load_data import load_set
from quote_check import quote_found

FACTS_DIR = Path(__file__).parent.parent / "data" / "facts"


def check_facts(facts: list[Fact], pages: dict[str, str], company_name: str, domain: str,
                source: str = "website") -> list[dict]:
    """Run both checks on every fact - keep rejected facts too, with the reason."""
    results = []
    for fact in facts:
        if not quote_found(fact, pages):
            status, reason = "rejected", "quote not found in source page"
        else:
            verdict = llm_supports(fact, company_name, domain, source)
            status = "verified" if verdict.supported else "rejected"
            reason = verdict.reason
        results.append({**fact.model_dump(), "source": source, "status": status, "reason": reason})
    return results


if __name__ == "__main__":
    out_dir = FACTS_DIR / "website"
    out_dir.mkdir(parents=True, exist_ok=True)
    set_name = sys.argv[1] if len(sys.argv) > 1 else "dev"
    for _, company in load_set(set_name).iterrows():
        name, domain = company["company_name"], company["company_domain"]
        print(name)
        if not (PAGES_DIR / f"{domain}.json").exists():
            print("  no saved website pages")
            continue
        pages = load_pages(domain)
        facts = extract_facts(name, domain, pages, "its own website text")
        results = check_facts(facts, pages, name, domain)
        (out_dir / f"{domain}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        verified = sum(r["status"] == "verified" for r in results)
        print(f"  {verified} verified, {len(results) - verified} rejected")
