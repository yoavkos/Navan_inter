# Lead Tier Routing

AI-assisted tier assessment and routing recommendations for new business-travel customers.
A home assignment for Navan, Full-Stack Software Engineer, Growth AI Solutions.

**Author:** Yoav Sternik · November 2026

## What it does

New customers get a support tier from two inputs: the travel spend they declare and an estimated headcount. Both can be wrong. This system checks them:

1. **Signup:** the tier from the rules, plus first flags.
2. **Research:** the company's website and independent sources.
3. **Prove:** keep only facts with a quote and a source.
4. **Recommend:** 🟢 tier fits, 🟡 needs a look, or 🔴 consider a higher tier, with a short sourced note.
5. **Re-check:** after 30 days, using real bookings.

The system never changes a tier. A person always decides.

## What to read

| File | What it is |
|---|---|
| [`process/system-spec.md`](process/system-spec.md) | **Start here.** The product spec: problem, design, evaluation, next steps |
| [`process/ai-appendix.md`](process/ai-appendix.md) | AI tools used, the prompts, a representative output, and how prompts were refined |
| [`process/independent-research.md`](process/independent-research.md) | 5 companies researched by hand, compared with the system |
| [`process/architecture.svg`](process/architecture.svg) | Architecture diagram |

## Project structure

```
src/        Python code. Files starting with ai_ call the model
data/       Saved pages, extracted facts, recommendations and evaluation results
process/    Spec, AI appendix, independent research and the diagram
deck/       Source files of the presentation
```

**Main files in `src/`:**

| Step | Files |
|---|---|
| Signup | `tier_rules.py`, `signup_flags.py` |
| Research | `website_scraper.py`, `ai_fact_extractor.py`, `ai_web_search.py`, `website_agent.py`, `search_agent.py` |
| Prove | `ai_entity_check.py`, `quote_check.py`, `ai_fact_verifier.py`, `evidence.py` |
| Recommend | `decision_rules.py`, `ai_judge.py`, `recommend.py`, `ai_note_writer.py` |
| Re-check | `day30_review.py` |
| Evaluation | `evaluate.py` |

## How to run

Requires Python 3.12 and an Anthropic API key. The prospects CSV from the assignment goes in the project root, under its original name (`Candidate_Exercise_—_Growth_Prospect_Signals_-_Prospects.csv`).

```bash
pip install pandas requests beautifulsoup4 anthropic pydantic pycountry
```

```bash
export ANTHROPIC_API_KEY=...
```

From `src/`, for the dev set (`dev`) or the test set (`test`):

```bash
python save_website_pages.py dev
```

```bash
python website_agent.py dev
```

```bash
python search_agent.py dev
```

```bash
python recommend.py
```

```bash
python evaluate.py expected_dev.csv
```

```bash
python day30_review.py
```

`signup_flags.py`, `decision_rules.py` and `day30_review.py` use no AI and cost nothing to run.

## AI tools used

- **Claude Code:** planning, writing the code and web research.
- **ChatGPT:** a second opinion on the plan at the start.
- **Claude Haiku 5.5:** the model inside the system, chosen for speed and low cost.
