# Independent research: 5 companies

**Goal:** set an expected answer for 5 companies **without the system**, then compare it with what the system said.
**Method:** a plain web search per company (2026-11-14), outside the project code. Headcounts come from third-party sites and are estimates.
**Tier rules:** Tier 1 at $500K+ GBV. Tier 2 at $100K+ GBV or 150+ employees. Tier 3 otherwise.

| Company | File | What the research found | Expected | System (dev, 3 runs) | Match |
|---|---|---|---|---|---|
| Attio | Tier 3, $47K, 24 employees | ~170–176 employees (Revelio Labs, TipRanks, Dealroom). Above 150, so Tier 2. | 🔴 | 🔴 🔴 🔴 | ✅ |
| Valarian | Tier 1, $510K, 175 employees | 10–32 employees (Dealroom, Rocketlist, RocketReach). $510K is a lot for ~30 people. | 🟡 | 🟡 🟡 🟡 | ✅ |
| Instinct | Tier 3, $35K, size missing | $1B Series C at $10B (Sept 2026), a month after a $250M Series B at $2.5B. ~14 employees (one secondhand report). | 🟡 high priority | 🟡 🟡 🟡 | ✅ |
| Ageas Retail | Tier 2, $140K, size missing | Owned by Ageas (UK), part of the Brussels-based Ageas Group. Declared spend may cover this entity only. | 🟡 | 🟡 🟡 🟡 | ✅ |
| Recraft | Tier 2, $168K, size missing | 38–56 employees, about $42M raised (Series B, 2025). Fits Tier 2. | 🟢 | 🟡 🟢 🟡 | ❌ |

**Result:** 4 of 5 match. Recraft is a false positive, and also unstable across runs.

**What reality showed later (day-30 bookings):**
- **Attio:** $76K–176K a year. The high estimate reaches Tier 2, so the bookings partly support the research.
- **Valarian:** $475K–1.1M a year, which fits Tier 1. The spend doubt was cleared: the file's headcount was wrong, not the spend.

## Sources
- Attio: [Revelio Labs](https://www.reveliolabs.com/companies/attio/employees), [TipRanks](https://www.tipranks.com/private-companies/attio), [Dealroom](https://dealroom.co/companies/attio/)
- Valarian: [Dealroom](https://dealroom.co/companies/valarian/), [Rocketlist](https://rocketlist.ai/companies/valarian), [RocketReach](https://rocketreach.co/valarian-profile_b711d831c4a58d75)
- Instinct: [TechCrunch](https://techcrunch.com/2026/09/28/viral-ai-agent-instinct-raises-1b-series-c-at-a-10b-valuation), [The Star](https://www.thestar.com.my/tech/tech-news/2026/09/28/ai-agent-firm-instinct-raises-1-billion-in-latest-funding-round)
- Ageas Retail: [Ageas executive team](https://www.ageas.co.uk/about-ageas/our-executive-team/), [Endole](https://open.endole.co.uk/insight/company/01324965-ageas-retail-limited), [Wikipedia](https://EN.wikipedia.com/wiki/Ageas)
- Recraft: [Business Wire](https://www.businesswire.com/news/home/20250430996607/en/Recraft-Raises-%2430M-Series-B-to-Bring-Creative-Quality-and-Brand-Control-to-Generative-AI-Design), [Rocketlist](https://rocketlist.ai/companies/recraft), [Dealroom](https://dealroom.co/companies/recraft/)
