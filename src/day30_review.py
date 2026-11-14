import re

from load_data import load_prospects
from signup_flags import gbv_tier
from tier_rules import Tier, is_higher

COST_PER_BOOKING = (300, 700)  # USD range - GBTA average trip ~$1,128, about 2-3 bookings per trip
DECLINE_PCT = -20               # bookings drop in days 16-30 that suggests an adoption problem
MINUS_SIGNS = "-−"         # the file uses the Unicode minus sign, not only the regular hyphen


def parse_activity(text: str) -> dict | None:
    """Travelers, bookings and trend % from the 30-day activity text - None if any value is missing."""
    travelers = re.search(r"(\d+) travelers?", text)
    bookings = re.search(r"(\d+) bookings", text)
    trend = re.search(rf"([+{MINUS_SIGNS}]\d+)%", text)
    if not (travelers and bookings and (trend or "flat" in text)):
        return None
    trend_pct = float(trend.group(1).replace("−", "-")) if trend else 0.0
    return {"travelers": int(travelers.group(1)), "bookings": int(bookings.group(1)), "trend_pct": trend_pct}


def annual_range(bookings: int) -> tuple[int, int]:
    """Yearly spend range estimated from one month of bookings."""
    return bookings * 12 * COST_PER_BOOKING[0], bookings * 12 * COST_PER_BOOKING[1]


def day30_recommendation(row) -> dict:
    """Re-check the tier with real travel activity - red only when even the low estimate is a higher tier."""
    activity = parse_activity(row["activity_30d"])
    if activity is None:
        return {"color": "yellow", "reasons": ["Activity text could not be read - check it manually."]}

    current = Tier(row["current_tier"])
    low, high = annual_range(activity["bookings"])
    tier_low, tier_high = gbv_tier(low), gbv_tier(high)
    reasons = [f"{activity['bookings']} bookings by {activity['travelers']} travelers in 30 days "
               f"-> about ${low:,}-${high:,} a year (declared ${row['gbv']:,})."]

    if is_higher(tier_low, current):
        color = "red"
        reasons.append(f"Even the low estimate is Tier {tier_low.value}; file says Tier {current.value}.")
    elif is_higher(tier_high, current):
        color = "yellow"
        reasons.append(f"The high estimate reaches Tier {tier_high.value} - may be outgrowing Tier {current.value}.")
    elif is_higher(current, tier_high):
        color = "yellow"
        reasons.append(f"Even the high estimate is Tier {tier_high.value} - activity is below Tier {current.value}.")
    else:
        color = "green"
        reasons.append(f"Activity fits Tier {current.value}.")

    if activity["trend_pct"] <= DECLINE_PCT:
        color = "red" if color == "red" else "yellow"
        reasons.append(f"Bookings fell {activity['trend_pct']:.0f}% in days 16-30 - adoption risk, customer success should reach out.")
    return {"color": color, "reasons": reasons}


if __name__ == "__main__":
    df = load_prospects()
    for _, row in df[df["activity_30d"].notna()].iterrows():
        result = day30_recommendation(row)
        print(f"{result['color'].upper():<7} {row['company_name']} (Tier {row['current_tier']})")
        for reason in result["reasons"]:
            print(f"        - {reason}")
