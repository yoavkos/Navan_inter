import re
from urllib.parse import urlparse

import pycountry

from evidence import consolidate_employees, employee_estimates, load_verified_facts
from load_data import DEV_SET_IDS, load_prospects
from signup_flags import MISSING_SIZE, signup_flags
from tier_rules import Tier, is_higher, rule_tier

# Research flags - based only on verified facts
SIZE_SUGGESTS_HIGHER_TIER = "SIZE_SUGGESTS_HIGHER_TIER"  # Confirmed employee count gives a higher tier
SIZE_SUGGESTS_LOWER_TIER = "SIZE_SUGGESTS_LOWER_TIER"    # Confirmed employee count gives a lower tier
SOURCES_CONFLICT = "SOURCES_CONFLICT"                    # Sources disagree on employees across a tier threshold
HAS_PARENT_COMPANY = "HAS_PARENT_COMPANY"                # Verified parent - declared GBV may be partial
MULTI_COUNTRY = "MULTI_COUNTRY"                          # 3+ verified countries, company in Tier 3

MIN_COUNTRIES = 3
# Short names and cities that pycountry doesn't know - everything else comes from pycountry
COUNTRY_ALIASES = {
    "uk": "United Kingdom", "britain": "United Kingdom", "england": "United Kingdom",
    "scotland": "United Kingdom", "wales": "United Kingdom", "london": "United Kingdom",
    "us": "United States", "usa": "United States", "america": "United States",
}


def site(url: str) -> str:
    """Short source name for explanations - e.g. 'pitchbook.com'."""
    return urlparse(url).netloc.removeprefix("www.")


def country_of(part: str) -> str | None:
    """Official country name found in a short text like 'London HQ' or 'Spain' - None if not recognized."""
    for word in re.findall(r"[a-z]+", part.lower()):
        if word in COUNTRY_ALIASES:
            return COUNTRY_ALIASES[word]
    for country in pycountry.countries:
        if re.search(rf"\b{re.escape(country.name.lower())}\b", part.lower()):
            return country.name
    return None


def countries_in(facts: list[dict]) -> tuple[set[str], list[str]]:
    """Return (distinct countries, unrecognized text parts) from verified 'countries' facts."""
    found, unknown = set(), []
    for fact in facts:
        if fact["field"] == "countries":
            for part in re.split(r",|;|/|\(|\)| and | plus ", fact["value"]):
                if part.strip():
                    country = country_of(part)
                    found.add(country) if country else unknown.append(part.strip())
    return found, unknown


def research_flags(row, facts: list[dict]) -> tuple[list[str], list[str], list[str], int | None]:
    """Return (flags, reasons, notes, confirmed employees) - notes give context but don't change the color."""
    flags, reasons, notes = [], [], []
    current = Tier(row["current_tier"])
    estimates = employee_estimates(facts)
    confirmed, conflict = consolidate_employees(estimates)
    sources = ", ".join(f"{n:,} ({s})" for s, n in estimates.items())

    if confirmed:
        research_tier = rule_tier(row["gbv"], confirmed)
        if is_higher(research_tier, current):
            flags.append(SIZE_SUGGESTS_HIGHER_TIER)
            reasons.append(f"Confirmed ~{confirmed:,} employees [{sources}] gives Tier {research_tier.value} "
                           f"by the tier rules; file says Tier {current.value} ({row['employees']} employees).")
        elif is_higher(current, research_tier):
            flags.append(SIZE_SUGGESTS_LOWER_TIER)
            reasons.append(f"Confirmed ~{confirmed:,} employees [{sources}] gives Tier {research_tier.value}; "
                           f"file says Tier {current.value}.")
    if conflict:
        low, high = min(estimates.values()), max(estimates.values())
        if rule_tier(row["gbv"], low) != rule_tier(row["gbv"], high):  # only if it could change the tier
            flags.append(SOURCES_CONFLICT)
            reasons.append(f"Sources disagree on employee count across a tier threshold: {sources}.")

    funding = {f["value"]: site(f["source_url"]) for f in facts if f["field"] == "funding"}
    if funding:  # always a note - growth is judged by the AI reviewer
        notes.append("Verified funding: " + "; ".join(f"{v} ({s})" for v, s in list(funding.items())[:3]) + ".")

    parents = [f for f in facts if f["field"] == "parent_company"]
    if parents:
        flags.append(HAS_PARENT_COMPANY)
        reasons.append(f"Part of {parents[0]['value']} ({site(parents[0]['source_url'])}) - declared GBV may cover only this entity.")

    countries, unknown = countries_in(facts)
    if len(countries) >= MIN_COUNTRIES and current == Tier.TIER_3:
        flags.append(MULTI_COUNTRY)
        reasons.append(f"Operates in {len(countries)} countries: {', '.join(sorted(countries))}.")
    if unknown:
        notes.append(f"Location text not recognized as a country: {', '.join(repr(u) for u in unknown)}.")

    return flags, reasons, notes, confirmed


def rules_recommendation(row) -> dict:
    """Rules-only recommendation (red / yellow / green) with the reasons behind it."""
    facts = load_verified_facts(row["company_domain"])
    flags, reasons, notes, confirmed = research_flags(row, facts)

    signup_row = row.copy()
    if confirmed:
        signup_row["employees"] = confirmed  # research replaces the signup size estimate
    for flag in signup_flags(signup_row):
        if flag == MISSING_SIZE:
            notes.append("No employee data found - no reason to change the tier.")
            continue  # no evidence, no flag
        flags.append(flag)
        reasons.append(f"Signup check: {flag} (GBV ${row['gbv']:,}, employees {signup_row['employees']}).")

    if SIZE_SUGGESTS_HIGHER_TIER in flags:
        color = "red"
    elif flags:
        color = "yellow"
    else:
        color = "green"
        reasons.append(f"No flags - research is consistent with Tier {row['current_tier']}.")
    return {"color": color, "flags": flags, "reasons": reasons, "notes": notes}


if __name__ == "__main__":
    df = load_prospects()
    for _, row in df[df["scenario_id"].isin(DEV_SET_IDS)].iterrows():
        result = rules_recommendation(row)
        print(f"{result['color'].upper():<7} {row['company_name']} (Tier {row['current_tier']})")
        for reason in result["reasons"]:
            print(f"        - {reason}")
        for note in result["notes"]:
            print(f"        (note) {note}")
