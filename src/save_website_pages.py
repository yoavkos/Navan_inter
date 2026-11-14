import json
import sys
from pathlib import Path

from load_data import load_set
from website_scraper import collect_company

PAGES_DIR = Path(__file__).parent.parent / "data" / "pages"

if __name__ == "__main__":
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    set_name = sys.argv[1] if len(sys.argv) > 1 else "dev"
    for _, company in load_set(set_name).iterrows():
        domain = company["company_domain"]
        print(company["company_name"])
        try:
            pages = collect_company(domain)
        except Exception as error:
            print(f"  FAILED ({error})")
            continue
        (PAGES_DIR / f"{domain}.json").write_text(json.dumps(pages, indent=2), encoding="utf-8")
        print(f"  saved {len(pages)} pages")
