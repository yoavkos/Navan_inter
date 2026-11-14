from enum import IntEnum

import pandas as pd

from load_data import load_prospects


class Tier(IntEnum):
    # Note: lower number = higher tier (more support). Use is_higher() to compare.
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


def is_higher(a: Tier, b: Tier) -> bool:
    """True if tier a gets more support than tier b (Tier 1 is the highest)."""
    return a < b


TIER1_GBV = 500_000
TIER2_GBV = 100_000
TIER2_EMPLOYEES = 150


def rule_tier(gbv: int, employees) -> Tier:
    """Return the tier from the assignment rules (GBV and employee thresholds)."""
    if gbv >= TIER1_GBV:
        return Tier.TIER_1
    if gbv >= TIER2_GBV or (pd.notna(employees) and employees >= TIER2_EMPLOYEES):
        return Tier.TIER_2
    return Tier.TIER_3


if __name__ == "__main__":
    df = load_prospects()
    df["rule_tier"] = df.apply(lambda r: rule_tier(r["gbv"], r["employees"]), axis=1)
    mismatches = df[df["rule_tier"] != df["current_tier"]]
    print(f"Mismatches: {len(mismatches)} of {len(df)}")
    print(mismatches[["scenario_id", "company_name", "gbv", "employees", "current_tier", "rule_tier"]].to_string(index=False))
