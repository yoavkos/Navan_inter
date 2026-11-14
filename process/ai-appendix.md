# AI Appendix

*How AI is used in the system: the tools, the roles, the agent, the constraints, the prompts and the output formats. Prompts are copied from `src/`. Example outputs are real and saved in `data/examples/instinct.json` and `data/facts/`.*

---

## 1. AI tools used

| Where | Tool | Used for |
|---|---|---|
| Development | **Claude Code** (Anthropic) | Planning, writing the code and web research |
| Development | **ChatGPT** (OpenAI) | A second opinion on the plan at the start |
| Inside the system | **Claude Haiku 5.5** (Anthropic API) | All six AI roles below. Chosen for speed and low cost |

---

## 2. The AI roles in the system

Each AI call does one narrow task and returns a fixed format. Code checks every result before it is used.

| # | Role | File | Input | Output | Checked by code |
|---|---|---|---|---|---|
| 1 | **Search agent** | `ai_web_search.py` | Company name and domain | Up to 5 URLs | Keeps only URLs that appeared in the real search results, and drops the company's own site |
| 2 | **Right company?** | `ai_entity_check.py` | First 3,000 characters of a page | `about_company` + reason | Pages that fail are dropped before extraction |
| 3 | **Fact extractor** | `ai_fact_extractor.py` | Page text | Facts, each with an exact quote | The quote must appear on the cited page |
| 4 | **Verifier** | `ai_fact_verifier.py` | One fact and its quote | `supported` + reason | Only supported facts are kept. A number is confirmed only when two sources agree |
| 5 | **AI reviewer** | `ai_judge.py` | Signup data and all verified facts, with dates | 🟢 🟡 🟠 🔴 + reason | Combined with the rules. The AI alone can never produce red |
| 6 | **Note writer** | `ai_note_writer.py` | The decision, the reasons and the facts | A short note | Every number in the note must appear in its input |

---

## 3. The agent

**The search agent is the only place where the model chooses its own steps.** It gets the `web_search` tool and decides what to search for, up to 3 searches per company.

| | |
|---|---|
| Tool | `web_search_20250305`, `max_uses: 3` |
| Model decides | Which queries to run, which results to return |
| Code decides | Which URLs are kept: only those the search really returned, and none from the company's own domain |
| Then | Code downloads the pages and skips blocked or empty ones. Role 2 checks each page is about the right company |

**Why only here:** searching needs choices that can't be fixed in advance. Every other step has one input and one answer, so a single narrow call is safer and easier to test.

---

## 4. Constraints we imposed on the model

| Constraint | Why | Where |
|---|---|---|
| **One narrow task per call** | Easier to check and to test | All roles |
| **A fixed output format** (structured outputs with Pydantic) | No free text to parse; a missing field fails loudly | All roles |
| **Use only the given text, no outside knowledge** | Prevents invented facts | Extractor, reviewer |
| **Copy the quote exactly, word for word** | Lets code find the quote on the page | Extractor |
| **"Not found" is a valid answer: never guess** | Missing is better than invented | Extractor |
| **Field definitions** (e.g. countries = where the company itself has staff) | The same word can mean different things | Extractor, verifier |
| **Reason first, then the answer** (`reason` comes before the verdict in every schema) | The answer follows the reasoning, and a person can read why | Right company, verifier, reviewer |
| **Only the start of a page** (3,000 characters) | A page's identity is set at its top; cheaper | Right company |
| **Today's date and the date of each fact** | Lets the reviewer judge how fast things change | Reviewer |
| **Red only for a higher tier** | A lower tier is never urgent; use orange | Reviewer |
| **At most 2 sentences and 40 words, start with why** | Written for a busy sales team | Note writer |
| **Use numbers exactly as given, never add new ones** | Code can check every number | Note writer |

---

## 5. Example: one company end to end

**Case: Instinct** (instinct.com). Declared spend $35K, no headcount, Tier 3. A generic name and a near-empty website make it ambiguous.

**1. Search agent:** 5 URLs, all from the real search results.
```json
["https://www.citybiz.co/article/910159/instinct-raises-1-billion-at-10-billion-valuation-with-14-employees/",
 "https://www.crunchbase.com/organization/instinct-9264",
 "https://pitchbook.com/profiles/company/1388308-78",
 "https://baike.baidu.com/en/item/Instinct/6089139",
 "https://seedtable.com/companies/instinct-ai/funding-rounds/series-c-2026-09"]
```

**2. Right company?**
```json
{
  "reason": "The page is an article focused on Instinct, a San Francisco personal AI assistant startup, covering its $1 billion Series C funding, valuation, employee count, and product features, which matches the target company instinct.com.",
  "about_company": true
}
```

**3 + 4. Extractor and verifier:** a fact, as saved after both steps.
```json
{
  "field": "employees",
  "value": "14",
  "quote": "The company has just 14 employees, according to Seeking Alpha.",
  "source_url": "https://www.citybiz.co/article/910159/...",
  "source_date": "September 28, 2026",
  "status": "verified",
  "reason": "The quote states the company has just 14 employees, attributed to Seeking Alpha, and refers to the company itself, so the claimed employee count of 14 is directly supported."
}
```

**5. AI reviewer:** 🟠 orange.
```json
{
  "reason": "Declared GBV is $35,000 and three sources (citybiz.co Sept 28 2026, pitchbook.com, multiples.vc) agree on 14 employees, both below Tier 2 thresholds, so Tier 3 fits on spend and headcount. However, funding moved from a $50M seed valuation (April 2026) to a $250M Series B at $2.5B (August 2026) to a $1B Series C at $10B (September 2026), which is unusually fast dated growth that a person should review, even though the 14-employee count contradicts it.",
  "color": "orange"
}
```
The rules said 🟢, because the hard numbers fit Tier 3. AI orange → 🟡 with high priority.

**6. Note writer:** what the sales team sees.
> 🟡 **Review needed - high priority.** Funding grew unusually fast: $50 million seed valuation (multiples.vc) to $10 billion Series C valuation (baike.baidu.com) within months, though headcount of 14 (citybiz.co) fits Tier 3. Evidence is mixed; verify the funding timeline.

*Code confirmed that every number in the note appears in its input.*

---

## 6. Output formats

```python
class SourceList(BaseModel):      # 1. Search agent
    urls: list[str]

class PageVerdict(BaseModel):     # 2. Right company?
    reason: str
    about_company: bool

class Fact(BaseModel):            # 3. Extractor (returned as Facts: list[Fact])
    field: Literal["employees", "industry", "countries", "parent_company", "funding", "hiring"]
    value: str
    quote: str
    source_url: str
    source_date: str | None

class Verdict(BaseModel):         # 4. Verifier
    reason: str
    supported: bool

class Judgment(BaseModel):        # 5. AI reviewer
    reason: str
    color: Literal["green", "yellow", "orange", "red"]

class Note(BaseModel):            # 6. Note writer
    text: str
```

---

## 7. How the prompts were refined

*One thread: every fix was checked for what it broke.*

### The verifier, in three versions
**The ambiguous case:** Greyparrot's homepage says *"80+ materials recovery facilities across 20+ countries."* Are these the company's countries, or its customers'?

| Version | Result | Diagnosis | Fix |
|---|---|---|---|
| 1 | ❌ Accepted "20+ countries" | The prompt never said what "countries" means | Field definitions in **both** the extractor and the verifier: *"countries where the company itself has offices or staff. Countries of customers… do NOT count."* |
| 2 | ✅ Rejected it. ❌ But also rejected *"Dalkia UK employs around 5,300 people"* | Name in file (Dalkia Facilities) ≠ name in quote (Dalkia UK) | *"The quote is from the company's own website. Name variants refer to this company."* |
| 3 | ✅ Both right. Only 3 rejections across 11 companies, all justified | - | - |

**Bonus catch in version 3:** a page showed a truncated headline, "$45 ...". The extractor filled in "$45 million". The verifier rejected it: the number was not in the text.

### External pages: one check per page
*The same over-strictness came back on external sources.* Profile lines like *"Employees 108"* were rejected because the line itself doesn't name the company. We added a single check per page: is the whole page about this company? On the same pages:
- verified facts went from **38 → 80**;
- rejections went from **51 → 10**.

### A change that was reverted
*This time, fixing one case broke four others.* Two clarifications to the reviewer fixed one over-cautious case (Balfour Beatty). On the next run the reviewer **missed real signals** in four companies, for example a $510K declared spend for a 31-person company. The change was reverted. **From then on, every change was judged on a fixed set of companies with expected answers, not case by case.**

### A limit that remains
In an earlier run, a note called a $50M valuation a "$50 million seed". The number check passed, because the number was real. **Code checks that a number exists, not what it means.** The run above shows the correct wording, but the gap is still open.

---

## 8. Guardrails: AI output is never trusted unchecked

| AI output | Checked by code |
|---|---|
| A link from search | Must have appeared in the actual search results |
| A quote | Must appear word for word on the cited page |
| A number in the note for the sales team | Must appear in the evidence given to the AI |
| The recommendation color | Set by the combine rule. The AI alone can never produce red |

**Results on all 43 companies, 3 runs each:**
- **0** notes contained an unsupported number.
- **39 of 458** extracted facts were rejected by the checks, so they never reached a decision.

---

## 9. The prompts

*Copied from `src/`. Words in `{braces}` are filled in by code.*

### 1. Search agent (`ai_web_search.py`)
```text
Find independent sources about this company: {company_name} ({domain}).
Look for: number of employees, offices and countries, funding rounds, parent company, industry.
Prefer news articles, company registries and Wikipedia.
Do NOT return pages from {domain} itself.
Make sure each source is about this company, not another company with a similar name.
Return up to 5 URLs.
```

### 2. Right company? (`ai_entity_check.py`)
```text
Is this web page mainly about the company {company_name} ({domain})?
Answer about_company=true only if the page is clearly about this specific company -
not another company with a similar name, and not a list of many companies.
First give a one-sentence reason, then the answer.

Page ({url}):
{text}
```

### 3. Fact extractor (`ai_fact_extractor.py`)
```text
You extract facts about a company from {source_description}.

Company: {company_name} ({domain})

Field definitions:
- employees: number of people working at the company itself.
- industry: what the company itself does or sells.
- countries: countries where the company itself has offices or staff.
  Countries of customers, users, installations or sales do NOT count.
- parent_company: a company that owns this company.
- funding: money the company itself raised (investment round, grant).
- hiring: the company itself is recruiting (open roles, "we're hiring").

Rules:
1. Use ONLY the text below. Do not use your own knowledge.
2. "quote" must be copied EXACTLY from the text, word for word.
3. If a field is not clearly stated, do not return it. Never guess.
4. If the text does not seem to be about this company, return no facts.
5. source_url: the URL in the "---" header above the quote.
6. source_date: only if a date appears in the text near the quote, else null.

Pages:
{pages}
```

### 4. Verifier (`ai_fact_verifier.py`)
```text
You check whether a quote supports a fact about a company.

Company: {company_name}
{source_context}

{field definitions, as above}

Field: {field}
Claimed value: {value}
Quote: "{quote}"

Answer supported=true only if the quote directly states this value about the company itself
(not about its customers, partners, products or market).
First give a one-sentence reason, then the answer.
```
`{source_context}` for the company's own website:
```text
The quote comes from the company's own website ({domain}).
Statements without a company name, or with a name variant (e.g. "Dalkia UK"), refer to this company.
```
For an external page:
```text
The quote comes from an external page that was checked and is about this company ({domain}).
Statements without a company name refer to this company, unless the quote names a different company.
```

### 5. AI reviewer (`ai_judge.py`)
```text
You review a new business-travel customer and recommend whether its support tier fits.
Today is {today}.

Tiers:
- Tier 1: $500K+ annual travel spend (GBV) - dedicated account executive and account manager.
- Tier 2: $100K-$500K GBV, or 150+ employees - an account executive drives adoption.
- Tier 3: everything else - self-serve, product-led.

Signup data (entered by the customer or estimated):
- Company: {company_name} ({domain})
- Declared annual GBV: ${gbv}
- Estimated employees: {employees}
- Current tier: Tier {tier}

Verified research facts (each checked against its source, with its date when known):
{facts}

Weigh both numbers and softer signals (industry and how much it travels, international presence,
growth and its timing, parent company, contradictions between sources). Use only the data above.

Recommend one level:
- green: the current tier fits the evidence.
- yellow: a minor concern worth a glance (weak or general doubts), but no specific evidence the tier is wrong.
- orange: a strong concern a person should review soon - specific evidence the tier may not fit,
  or dated evidence of unusually fast or large change (for example rapid funding growth or fast hiring).
- red: strong evidence from 2+ independent sources that the company belongs in a HIGHER tier.
  Never use red for a lower tier - use orange.

First write a short reason (2-3 sentences) naming the facts and dates you relied on, then the level.
```

### 6. Note writer (`ai_note_writer.py`)
```text
Write a short note for a sales rep about {company_name} (current Tier {tier}).
The recommendation is already decided: {headline}. Do not change it - explain it.

Rules reasons:
{rules_reasons}

AI reviewer reason:
{ai_reason}

Verified facts:
{facts}

Write at most 2 sentences and 40 words, plain English, for a busy sales rep:
- Do not repeat the recommendation - the rep already sees it as the headline. Start with WHY.
- Lead with the single most important fact, then at most one supporting fact.
- Give numbers with their source site in brackets, e.g. "206 employees (tracxn.com)".
- Use numbers exactly as they appear above. Never add numbers that are not above.
- No internal terms (flags, rules, signup check, AI reviewer, unrecognized locations).
- End with what to check, if anything, in a few words.
- {disagreement}
```
`{disagreement}` is either *"The two reviews disagreed - say in a few words that the evidence is mixed."* or *"Both reviews agree - do not mention any disagreement."*
