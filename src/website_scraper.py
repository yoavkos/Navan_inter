from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (company research script)"}
INFO_PAGES = {
    "about": ["about", "company"],
    "careers": ["careers", "jobs"],
    "contact": ["contact", "locations", "offices"],
    "news": ["news"],
    "sectors": ["sectors"],
    "modern_slavery": ["modern-slavery"],
}
SKIP_WORDS = ["leadership", "team", "people", ".pdf"]


def fetch_html(url: str) -> BeautifulSoup:
    """Download a page and return it as parsed HTML."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def find_info_links(html: BeautifulSoup, home_url: str) -> list[str]:
    """Return same-site links to info pages - at most one per page type."""
    home_domain = urlparse(home_url).netloc.removeprefix("www.")
    found = {}
    for link in html.find_all("a", href=True):
        url = urljoin(home_url, link["href"]).split("#")[0]
        path = urlparse(url).path.lower()
        same_site = urlparse(url).netloc.removeprefix("www.") == home_domain
        if not same_site or any(word in path for word in SKIP_WORDS):
            continue
        for page_type, words in INFO_PAGES.items():
            if page_type not in found and url not in found.values() and any(word in path for word in words):
                found[page_type] = url
    return list(found.values())


def extract_text(html: BeautifulSoup) -> str:
    """Return the visible page text, without scripts, styles, menus and footer."""
    for tag in html(["script", "style", "nav", "footer"]):
        tag.decompose()
    return " ".join(html.get_text(" ").split())


def collect_company(domain: str) -> dict[str, str]:
    """Download the home page and info pages of a company - returns {url: text}."""
    home_url = f"https://{domain}"
    home_html = fetch_html(home_url)
    urls = [home_url] + find_info_links(home_html, home_url)
    pages = {}
    for url in urls:
        try:
            pages[url] = extract_text(fetch_html(url))
        except Exception as error:
            print(f"  skipped {url} ({error})")
    return pages


if __name__ == "__main__":
    html = fetch_html("https://attio.com")
    print(find_info_links(html, "https://attio.com"))
