from ai_fact_extractor import Fact, load_pages

QUOTE_CHARS = {"’": "'", "‘": "'", "“": '"', "”": '"'}


def normalize(text: str) -> str:
    """Lowercase, unify quote marks and collapse spaces - so tiny copy differences don't fail the check."""
    for fancy, plain in QUOTE_CHARS.items():
        text = text.replace(fancy, plain)
    return " ".join(text.lower().split())


def quote_found(fact: Fact, pages: dict[str, str]) -> bool:
    """True if the fact's quote appears in the page it claims to come from."""
    page = pages.get(fact.source_url, "")
    return normalize(fact.quote) in normalize(page)


if __name__ == "__main__":
    pages = load_pages("greyparrot.ai")
    real = Fact(field="employees", value="over 50 people", source_date=None,
                quote="We're a team of over 50 people from 23 nationalities",
                source_url="https://www.greyparrot.ai/about-us")
    fake = Fact(field="employees", value="500", source_date=None,
                quote="We have 500 employees",
                source_url="https://www.greyparrot.ai/about-us")
    print(f"Real quote found: {quote_found(real, pages)}")
    print(f"Fake quote found: {quote_found(fake, pages)}")
