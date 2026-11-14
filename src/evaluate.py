import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from load_data import load_prospects
from recommend import final_recommendation

EVAL_DIR = Path(__file__).parent.parent / "data" / "eval"
FACTS_DIR = Path(__file__).parent.parent / "data" / "facts"
RUNS = 3


def unsupported_fact_rate(domains: list[str]) -> tuple[int, int]:
    """Return (rejected, total) extracted facts - facts the checks refused to support."""
    rejected = total = 0
    for domain in domains:
        for path in FACTS_DIR.glob(f"*/{domain}.json"):
            facts = json.loads(path.read_text(encoding="utf-8"))
            total += len(facts)
            rejected += sum(f["status"] != "verified" for f in facts)
    return rejected, total


def evaluate(expected_file: str) -> None:
    """Run the full recommendation several times per company and compare with the expected answers."""
    expected = pd.read_csv(EVAL_DIR / expected_file)
    df = load_prospects()
    rows = df.set_index("scenario_id").loc[expected["scenario_id"]].reset_index()

    results = []
    for (_, row), (_, exp) in zip(rows.iterrows(), expected.iterrows()):
        runs = [final_recommendation(row) for _ in range(RUNS)]
        colors = [r["final"] for r in runs]
        majority = Counter(colors).most_common(1)[0][0]
        results.append({
            "company": exp["company"],
            "expected": exp["expected_color"],
            "got": majority,
            "runs": "/".join(colors),
            "stable": len(set(colors)) == 1,
            "priority_ok": sum(r["priority"] == exp["expected_priority"] for r in runs) / RUNS,
            "agreement": sum(r["agreement"] for r in runs) / RUNS,
            "notes_ok": all(r["note"]["numbers_checked"] for r in runs),
        })
        print(f"  {exp['company']}: expected {exp['expected_color']}, got {'/'.join(colors)}")

    res = pd.DataFrame(results)
    flagged_exp = res["expected"] != "green"
    flagged_got = res["got"] != "green"
    rejected, total = unsupported_fact_rate(rows["company_domain"].tolist())

    print("\n=== Results (majority of", RUNS, "runs) ===")
    print(res[["company", "expected", "got", "runs", "stable"]].to_string(index=False))
    print("\n=== Metrics ===")
    print(f"Exact color match:        {(res['expected'] == res['got']).mean():.0%}")
    print(f"False positives (unneeded flags):  {(~flagged_exp & flagged_got).sum()} of {(~flagged_exp).sum()} expected green")
    print(f"False negatives (missed flags):    {(flagged_exp & ~flagged_got).sum()} of {flagged_exp.sum()} expected flagged")
    print(f"Red precision:            {((res['got'] == 'red') & (res['expected'] == 'red')).sum()} of {(res['got'] == 'red').sum()} reds correct")
    print(f"Stable across runs:       {res['stable'].mean():.0%}")
    print(f"Rules-AI agreement:       {res['agreement'].mean():.0%}")
    print(f"Priority correct:         {res['priority_ok'].mean():.0%}")
    print(f"Notes with only supported numbers: {res['notes_ok'].mean():.0%}")
    print(f"Unsupported facts rejected by checks: {rejected} of {total} ({rejected / total:.0%})")
    res.to_csv(EVAL_DIR / expected_file.replace("expected", "results"), index=False)


if __name__ == "__main__":
    evaluate(sys.argv[1] if len(sys.argv) > 1 else "expected_dev.csv")
