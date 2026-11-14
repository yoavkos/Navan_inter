from pathlib import Path

import pandas as pd

DEV_SET_IDS = ["P-023", "P-007", "P-018", "P-014", "P-009", "P-012",
               "P-042", "P-022", "P-002", "P-021", "P-031"]

CSV_PATH = Path(__file__).parent.parent / "Candidate_Exercise_—_Growth_Prospect_Signals_-_Prospects.csv"


def load_prospects() -> pd.DataFrame:
    """Load the prospects CSV and clean column names, GBV and tiers (read-only)."""
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "entered_gbv_usd": "gbv",
        "ZI_company_size_est": "employees",
        "navan_travel_activity_30d_post_signup": "activity_30d",
    })
    df["gbv"] = df["gbv"].str.replace(r"[$,]", "", regex=True).astype(int)
    df["employees"] = df["employees"].astype("Int64")
    df["current_tier"] = df["current_tier"].str.extract(r"(\d)", expand=False).astype(int)  # "Tier 2" -> 2
    return df


def load_set(name: str) -> pd.DataFrame:
    """Companies of one set - 'dev' (used for building) or 'test' (held out until the end)."""
    df = load_prospects()
    in_dev = df["scenario_id"].isin(DEV_SET_IDS)
    return df[in_dev] if name == "dev" else df[~in_dev]


if __name__ == "__main__":
    df = load_prospects()
    print(f"Companies: {len(df)}")
    print(f"With employee estimate: {df['employees'].notna().sum()}")
    print(f"With 30-day activity: {df['activity_30d'].notna().sum()}")
    print("\nCurrent tier counts:")
    print(df["current_tier"].value_counts().sort_index().to_string())
