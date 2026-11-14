import json
from pathlib import Path

from ai_judge import ai_judgment, format_facts
from ai_note_writer import ICONS, write_note
from decision_rules import rules_recommendation
from evidence import load_verified_facts
from load_data import DEV_SET_IDS, load_prospects

RECOMMENDATIONS_DIR = Path(__file__).parent.parent / "data" / "recommendations"


def combine(rules_color: str, ai_color: str) -> str:
    """User-facing color (3 levels) from rules and the AI's 4 levels.

    Red only when both say red. Rules' green wins over the AI's minor concern (yellow);
    the AI's strong concern (orange) wins over the rules' green. Everything else is yellow.
    """
    if rules_color == "red" and ai_color == "red":
        return "red"
    if rules_color == "green" and ai_color in ("green", "yellow"):
        return "green"
    return "yellow"


def final_recommendation(row) -> dict:
    """Combine rules and AI reviewer into one recommendation, then write the note."""
    rules = rules_recommendation(row)
    judge = ai_judgment(row)
    final = combine(rules["color"], judge.color)
    priority = "high" if judge.color == "orange" else "normal"
    agree = rules["color"] == ("yellow" if judge.color == "orange" else judge.color)
    facts_text = format_facts(load_verified_facts(row["company_domain"]))
    note = write_note(row["company_name"], int(row["current_tier"]), final, priority, agree,
                      rules["reasons"] + rules["notes"], judge.reason, facts_text)
    return {
        "company": row["company_name"],
        "current_tier": int(row["current_tier"]),
        "final": final,
        "priority": priority,
        "agreement": agree,
        "note": note,
        "rules": rules,
        "ai": judge.model_dump(),
    }


if __name__ == "__main__":
    RECOMMENDATIONS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_prospects()
    for _, row in df[df["scenario_id"].isin(DEV_SET_IDS)].iterrows():
        result = final_recommendation(row)
        (RECOMMENDATIONS_DIR / f"{row['company_domain']}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        status = "agree" if result["agreement"] else "DISAGREE"
        check = "" if result["note"]["numbers_checked"] else f"  [UNSUPPORTED NUMBERS: {result['note']['unsupported_numbers']}]"
        print(f"{result['company']} (Tier {result['current_tier']}) - rules {ICONS[result['rules']['color']]} "
              f"/ AI {ICONS[result['ai']['color']]} ({status})")
        print(f"   {result['note']['headline']}: {result['note']['text']}{check}\n")
