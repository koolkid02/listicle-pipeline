# SEO Listicle Generation Pipeline — Design README

**Project:** Zuddl, Lead Growth Engineering take-home
**Task:** Take a primary + secondary keyword input and produce a 95%-ready SEO listicle draft (e.g. *"Top X Event Registration & Ticketing Softwares"*), generalized across unrelated software categories.
**Status:** Architecture + synthetic data layer designed and built. Generation/formatting stages, human-in-the-loop tooling, and live retrieval are scoped but not yet implemented in code.

---

## 1. Problem framing

Every listicle in this format is fundamentally the same genre: **a ranked comparative study of N companies in one software category, dressed in SEO structure** (title, meta description, comparison table, per-company sections, FAQ, hyperlinks). Doing this by hand doesn't scale; doing it via raw LLM chat produces inconsistent output. The goal is a pipeline that is fast and consistent where the task is mechanical (retrieval, formatting) and hands control to a human wherever real judgment is required (which companies make the list, in what order, whether the data is current).

**Scope for this build:** 6 deliberately unrelated software categories, to prove the pipeline generalizes rather than being event-tech-specific:

1. Project Management Software
2. Hiring and HR Software
3. Event Registration and Ticketing Software
4. End-to-End CRM Software
5. Tax Filing Software
6. Email Marketing Software

---

## 2. Pipeline flow

```
User prompt
    │
    ▼
┌─────────────────────┐   no    ┌───────────────┐
│  Scope guardrail     │ ──────▶ │  Clarify       │──┐
│  (task in scope?)    │         │  ↻ to guardrail│  │
└─────────┬────────────┘         └────────────────┘  │
          │ yes                                       │
          ▼                                           │
┌──────────────────────────────┐  low   ┌─────────────▼──┐
│ Intent & confidence check    │ ─────▶ │  Confirm        │
│ → {category, confidence, KW} │        │  ↻ to guardrail │
└─────────┬─────────────────────┘        └─────────────────┘
          │ high confidence
          ▼
   ┌──────────────┬───────────────────┐
   ▼              ▼
┌─────────────┐ ┌──────────────────┐
│ Tools DB    │ │ LLM keyword       │
│ query       │ │ generation        │
│ (by category)│ │ (3 parallel calls:│
│             │ │  lexical/semantic/│
│             │ │  intent, live)    │
└──────┬──────┘ └────────┬─────────┘
       └───────┬──────────┘
               ▼
      ┌──────────────────┐
      │ Retrieval output  │
      │ (companies +      │
      │  generated KWs)   │
      └────────┬──────────┘
               ▼
      ┌──────────────────┐  fail   ┌─────────────────┐
      │ Human review      │ ──────▶│ Escalate         │
      │ (HITL)            │        │ ↻ to guardrail   │
      └────────┬──────────┘        └──────────────────┘
               │ pass
               ▼
        To summariser → formatter → publishable draft
```

**Design principle:** every guardrail failure and every HITL rejection routes back to the *same* scope guardrail rather than each having its own dead-end or its own recovery path. One re-entry point, one thing to build and test, instead of three different failure flows.

### Stage-by-stage

| Stage | What it does | Nature |
|---|---|---|
| Scope guardrail | Confirms the request is actually a listicle-generation task ("write me a listicle about X") and not something else | LLM classification, cheap, first line of defense |
| Intent & confidence check | Classifies the request against the 6 known categories, extracts the primary keyword, returns a confidence score | LLM classification against a closed set of 6 — deliberately *not* an open embedding search, since a fixed dictionary of 6 categories is more debuggable than nearest-neighbor matching at this scale |
| Tools DB query | `SELECT * FROM tools WHERE category = X` | Deterministic, boring on purpose — no live search, no hallucination risk |
| LLM keyword generation | Three parallel live LLM calls off the primary keyword — lexical, semantic, intent — each with its own prompt and temperature | **Live, not cached.** Runs at request time using the project's LLM API key. See §4b |
| Retrieval output | Merges the DB query and the generated keywords into one JSON handoff object | Decouples summarizer from however retrieval happens under the hood (today: fixed DB + live LLM calls; later: Tavily + live G2 API for the company side) |
| Human review (HITL) | Human adds/removes companies, sets final count, reorders, flags stale data | **Explicitly a human decision, not model judgment** — see §5 |
| Summariser | Turns structured retrieval output into flowing prose per section | Not yet built |
| Formatter | Slots prose into title / headings / table / FAQ / hyperlinks, runs SEO placement checks | Not yet built |

---

## 3. Data source decisions

| Source | Role | Why |
|---|---|---|
| G2 | Aggregate rating signal | Has a real public API (`data.g2.com`), but not integrated for this build — mimicked via a curated synthetic DB with the same shape, so swapping in the live API later doesn't require restructuring |
| Capterra | Aggregate rating signal | **No public API for product/review data** exists (their only public API is an unrelated ad-click analytics endpoint for vendors) — confirmed by direct research, also confirmed scraping is blocked (`g2.com/products/.../reviews` returned "Failed to fetch url" via Tavily extract) |
| Tavily | Live pricing + feature detail + citation URLs | Explicitly scoped to **Phase 2**, not used in this build |

**Explicitly out of scope:** review-level mining (pulling and summarizing individual reviewer text). Only aggregate rating + review count is captured. Review-text summarization is a Phase 2 idea (see §7).

---

## 4. One database + one live generation step

### 4a. `synthetic_tool_db.{json,csv}` — company facts

One row per company. **Synthetic data** — every company name, price, rating, and review count is fictional, built only to validate the schema and pipeline logic before real retrieval is wired in.

Fields: `company_name`, `category`, `positioning`, `starting_price`, `aggregated_rating`, `review_count`, `what_it_does_well` (3–5 bullets), `gaps` (1–2 bullets), `best_for`, `website_url`, `source_url`, `last_updated`, `days_since_update`.

~15–20 companies per category (103 total) — deliberately more than a typical top-8 listicle needs, so the human reviewer at the HITL step is making a real inclusion/exclusion call, not just reordering a fixed set.

`last_updated` / `days_since_update` exist so staleness is visible at the HITL step. **Not yet implemented:** an actual decay-weighted confidence score (e.g. `weight = e^(-days_since_update / half_life)`) that would feed a precomputed default ranking — currently a design decision, not code. Today ordering is whatever the query returns; the human sorts it.

### 4b. Keyword generation — live LLM calls, not a database

**Decision:** no `keyword_db`. With a project LLM API key available, keeping keyword generation as a precomputed, cached lookup table was a workaround for not having live access — it isn't the better design once live calls are on the table. Keywords are generated fresh at request time.

Three relationship types per request, each its own live LLM call, fired in parallel, off the primary keyword that came out of intent classification:

| Type | Purpose | Temperature | Why that temperature |
|---|---|---|---|
| **Lexical** | Shared words/phrases with the category name (`"project management tool"`, `"work management software"`) — goes in title, URL slug, first 100 words | 0.7 | Some variety helps catch natural phrasing (plurals, tool/platform/software swaps) a rigid algorithm would miss |
| **Semantic** | Related topic, different words (`"sprint planning"`, `"resource allocation"`) — goes in subheadings/body, proves topical depth | **0** | Deterministic on purpose — this is the block most likely to feed a ranking or a repeatability check downstream; nonzero temperature would make results drift call to call for the same input |
| **Intent** | Tagged by buyer-journey stage: `informational` / `commercial_investigation` / `comparison` — goes in FAQ (informational) and comparison table / best-for lines (commercial/comparison) | 0.7 | Natural buyer-phrasing variation, same reasoning as lexical |

Each call sends a fixed `prompt_template` (auditable, swappable independent of code) with the resolved category filled in, and returns structured JSON that gets parsed straight into the retrieval output — no intermediate storage.

**Tradeoff, stated honestly:** this trades the old design's speed and reproducibility (a cached lookup can't fail or drift) for freshness and flexibility (keywords can react to the actual request instead of being frozen at whatever they were when the DB was last built). It also adds three live API calls, and their latency, cost, and failure modes, to every single article request instead of once per category. Error handling for a failed or malformed keyword call becomes part of the runtime path, not something you can pre-validate offline.

**At request time**, the `Tools DB query` stays a plain, boring, deterministic read filtered by category. Keyword generation is the one genuinely live, non-deterministic step in retrieval, which is why it's drawn as its own parallel branch rather than folded into the same box as the DB query.

---

## 5. Human-in-the-loop checkpoints

Two identified so far, both hard stops (pipeline pauses, does not proceed silently):

1. **Scope / confidence guardrail failure** — if the request isn't clearly a listicle task, or the category match confidence is low, the agent states its allowed scope and asks the human to clarify, then re-enters at the same guardrail.
2. **Post-retrieval review** — before data is locked in for drafting, a human:
   - Adds or removes candidate companies
   - Sets the final company count (top-5 vs top-8, etc.)
   - Reorders the list — **ranking is explicitly a human decision, not model judgment**
   - Sanity-checks `last_updated` / pricing / ratings for anything stale enough to need a refresh

**Not yet designed:** a third checkpoint after drafting, for QA/humanization pass — this is an explicit brief requirement ("QA to humanise the writing") not yet addressed in this design.

---

## 6. What's built vs. what's designed-but-not-coded

**Built:**
- `synthetic_tool_db.json` / `.csv` — 103 synthetic companies across 6 categories
- Full pipeline flow design (this doc + diagram)

**Designed, not yet coded:**
- Intent classification + confidence-check LLM call
- Scope guardrail LLM call
- Live keyword generation calls (lexical / semantic / intent, 3 parallel prompts per request) — prompt templates and temperatures are designed (§4b); wiring them to the project's LLM API key is the next build step
- Decay-weighted default ranking for companies (currently just a raw `days_since_update` field, no computed score)
- HITL review UI/interface
- Summariser (structured data → prose)
- Formatter (prose → title/headings/table/FAQ/hyperlinks + automated SEO placement checks)
- Live Tavily / G2 API integration (Phase 2, company data only)

---

## 7. What breaks at scale / future scope

- **6 categories → 60 categories:** the closed-set classification approach (matching against a fixed list) stops being maintainable; would need embeddings or a proper classifier instead.
- **Review-level summarization:** currently only aggregate rating + count. Mining individual review text for themes is a real improvement but was cut for scope — G2/Capterra review scraping is blocked, and this would need the live G2 API.
- **Company-level keyword personalization:** keyword generation is category-level only for now. A future pass could generate lightweight per-company keyword variants (`"{company} pricing"`, `"{company} vs {competitor}"`) as part of the same live call, without needing a separate database.
- **Data freshness at scale:** with live retrieval (Tavily/G2 API) instead of a static synthetic DB, staleness handling becomes a real operational concern for the company data — the decay-weighted scoring design in §4a becomes necessary rather than optional.
- **Three live LLM calls per article request** for keyword generation is cheap at low request volume; at scale this is the pipeline's main latency and cost driver, since every request pays for fresh generation instead of a cache hit. Worth revisiting caching per (category, request-shape) if request volume grows, without going back to a single static precomputed table.

---

## 8. Files in this submission

| File | Contents |
|---|---|
| `synthetic_tool_db.json` / `.csv` | Company-level reference data, 103 rows, 6 categories |
| `README.md` | This document |
