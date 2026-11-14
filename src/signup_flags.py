import pandas as pd

from load_data import load_prospects
from tier_rules import TIER1_GBV, TIER2_GBV, TIER2_EMPLOYEES, Tier, is_higher, rule_tier

# Signup flags - triggers for research, not final decisions
MISSING_SIZE = "MISSING_SIZE"            # No employee estimate - tier relies on declared GBV only
GBV_LOW_FOR_SIZE = "GBV_LOW_FOR_SIZE"    # Declared GBV is low for the company size (employees x $667)
GBV_HIGH_FOR_SIZE = "GBV_HIGH_FOR_SIZE"  # Declared GBV is high for the company size (employees x $667)
NEAR_THRESHOLD = "NEAR_THRESHOLD"        # Within 20% below the next tier's threshold

GBV_PER_EMPLOYEE = TIER2_GBV / TIER2_EMPLOYEES
NEAR_MARGIN = 0.8


def gbv_tier(gbv: int) -> Tier:
    """Return the tier based on declared GBV only."""
    if gbv >= TIER1_GBV:
        return Tier.TIER_1
    if gbv >= TIER2_GBV:
        return Tier.TIER_2
    return Tier.TIER_3


def size_tier(employees: int) -> Tier:
    """Return the tier implied by employee count (employees x $667 GBV)."""
    return gbv_tier(employees * GBV_PER_EMPLOYEE)


def signup_flags(row) -> list[str]:
    """Return research-trigger flags for one company, using signup data only."""
    gbv, employees = row["gbv"], row["employees"]
    tier = rule_tier(gbv, employees)
    flags = []

    if pd.isna(employees):
        flags.append(MISSING_SIZE)
    elif is_higher(size_tier(employees), gbv_tier(gbv)):
        flags.append(GBV_LOW_FOR_SIZE)
    elif is_higher(gbv_tier(gbv), size_tier(employees)):
        flags.append(GBV_HIGH_FOR_SIZE)

    next_gbv = {Tier.TIER_2: TIER1_GBV, Tier.TIER_3: TIER2_GBV}.get(tier)
    if next_gbv and NEAR_MARGIN * next_gbv <= gbv < next_gbv:
        flags.append(NEAR_THRESHOLD)
    elif tier == Tier.TIER_3 and pd.notna(employees) and employees >= NEAR_MARGIN * TIER2_EMPLOYEES:
        flags.append(NEAR_THRESHOLD)

    return flags


if __name__ == "__main__":
    df = load_prospects()
    df["gbv_tier"] = df["gbv"].apply(gbv_tier)
    df["size_tier"] = df["employees"].apply(lambda e: size_tier(e) if pd.notna(e) else "-")
    df["flags"] = df.apply(signup_flags, axis=1)

    flagged = df[df["flags"].str.len() > 0]
    print(f"Research ratio: ${GBV_PER_EMPLOYEE:,.0f} per employee")
    print(f"Flagged for research: {len(flagged)} of {len(df)}\n")
    cols = ["scenario_id", "company_name", "gbv", "employees", "gbv_tier", "size_tier", "flags"]
    print(flagged[cols].to_string(index=False))
