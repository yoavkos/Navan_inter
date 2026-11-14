import json
import re
from pathlib import Path
from urllib.parse import urlparse

FACTS_DIR = Path(__file__).parent.parent / "data" / "facts"
AGREE_RATIO = 1.3
CONFLICT_RATIO = 2.0


def load_verified_facts(domain: str) -> list[dict]:
    """All verified facts about a company, from every agent's folder."""
    facts = []
    for path in FACTS_DIR.glob(f"*/{domain}.json"):
        facts += [f for f in json.loads(path.read_text(encoding="utf-8")) if f["status"] == "verified"]
    return facts


def parse_employees(value: str) -> int | None:
    """Number of employees from free text - '190+' -> 190, '11-50' -> 30, '13,700 in the UK' -> None."""
    if " in " in value.lower():
        return None
    numbers = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", value)]
    if not numbers:
        return None
    if len(numbers) >= 2 and "-" in value:
        return (numbers[0] + numbers[1]) // 2
    return numbers[0]


def employee_estimates(facts: list[dict]) -> dict[str, int]:
    """One employee number per source site - the first one found."""
    estimates = {}
    for fact in facts:
        number = parse_employees(fact["value"]) if fact["field"] == "employees" else None
        if number:
            estimates.setdefault(urlparse(fact["source_url"]).netloc.removeprefix("www."), number)
    return estimates


def consolidate_employees(estimates: dict[str, int]) -> tuple[int | None, bool]:
    """Return (confirmed count, conflict) - confirmed when the closest two sites agree within 30%."""
    values = sorted(estimates.values())
    conflict = len(values) >= 2 and max(values) / min(values) >= CONFLICT_RATIO
    pairs = [(max(a, b) / min(a, b), a, b) for a, b in zip(values, values[1:])]
    closest = min(pairs, default=None)
    if closest and closest[0] <= AGREE_RATIO:
        return (closest[1] + closest[2]) // 2, conflict
    return None, conflict
