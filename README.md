# SEO Listicle Generation Pipeline — Design README

**Task:** Take a primary + secondary keyword input and produce a 95%-ready SEO listicle draft (e.g. *"Top X Event Registration & Ticketing Softwares"*), generalized across unrelated software categories.
**Status:** Fully built and running end-to-end, as **two entry points sharing one
pipeline core** — a CLI (`main.py`) and a web app (FastAPI backend in `api/` + React
frontend in `frontend/`). Scope guardrail, intent classification, retrieval, live
keyword generation, human review, summariser, and formatter are all implemented; see
`docs/architecture.md` for the as-built component and request-flow diagrams. §6 below
has the full built-vs-not-built breakdown — the short version is that everything this
document originally scoped as "designed, not yet coded" is now built **except** live
Tavily/G2 retrieval, which was always explicitly deferred to a later phase and still is:
this build runs entirely on the synthetic dataset.

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

> **Revised during build, based on live testing:** this held for the guardrail/
> confidence-check loop, but a real HITL rejection routing all the way back to the
> guardrail turned out to be bad UX in practice — a person rejecting a company
> selection is almost never rejecting the category, just the selection, and typing
> selection-style input ("all", "1-5") into a "restate your request" prompt got
> misclassified as out-of-scope. The CLI's `human_review` reject path now loops back to
> `human_review` itself instead (a separate, bounded retry cap), while the guardrail/
> confidence loop is unchanged. See `docs/architecture.md` §1 for the current graph
> shape, and `src/listicle_pipeline/graph.py` for the actual routing.

This diagram is the pipeline as originally conceived. It's now built as **two separate
orchestrations sharing one core** — the CLI graph above (with real cycles and a
blocking terminal HITL step) and a stateless FastAPI backend (`api/`) that reuses the
exact same node functions but wires them into two small cycle-free graphs, since HITL
happens client-side in the web UI instead of as a blocking pipeline step. See
[`docs/architecture.md`](./docs/architecture.md) for the as-built component diagram and
a full request-flow sequence diagram, and [`docs/README.md`](./docs/README.md) for the
narrative walkthrough of what's shared vs. entry-point-specific.

### Stage-by-stage

| Stage | What it does | Nature |
|---|---|---|
| Scope guardrail | Confirms the request is actually a listicle-generation task ("write me a listicle about X") and not something else | LLM classification, cheap, first line of defense |
| Intent & confidence check | Classifies the request against the 6 known categories, extracts the primary keyword, returns a confidence score | LLM classification against a closed set of 6 — deliberately *not* an open embedding search, since a fixed dictionary of 6 categories is more debuggable than nearest-neighbor matching at this scale |
| Tools DB query | `SELECT * FROM tools WHERE category = X` | Deterministic, boring on purpose — no live search, no hallucination risk |
| LLM keyword generation | Three parallel live LLM calls off the primary keyword — lexical, semantic, intent — each with its own prompt and temperature | **Live, not cached.** Runs at request time using the project's LLM API key. See §4b |
| Retrieval output | Merges the DB query and the generated keywords into one JSON handoff object | Decouples summarizer from however retrieval happens under the hood (today: fixed DB + live LLM calls; later: Tavily + live G2 API for the company side) |
| Human review (HITL) | Human adds/removes companies, sets final count, reorders, flags stale data | **Explicitly a human decision, not model judgment** — see §5 |
| Summariser | Turns structured retrieval output into flowing prose per section | Built — `nodes/summariser.py`, one parallel LLM call per approved company |
| Formatter | Slots prose into title / headings / table / FAQ / hyperlinks, runs SEO placement checks | Built — `nodes/formatter.py` (prose) + `api/seo_checks.py` (placement checks, web app only) |

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

Three checkpoints now, all built, in both the CLI and the web app (mechanics differ per
surface — see below):

1. **Scope / confidence guardrail failure** — if the request isn't clearly a listicle
   task, or the category match confidence is low, the human is asked to clarify/pick a
   category and re-enters at the same guardrail. CLI: `nodes/guardrail.py` /
   `nodes/intent.py`'s `clarify`/`confirm`, blocking terminal `input()`. Web: the
   Guardrail screen's inline category picker, re-submitting `POST /pipeline/classify`.
2. **Post-retrieval review** — before data is locked in for drafting, a human:
   - Adds or removes candidate companies
   - Sets the final company count (top-5 vs top-8, etc.)
   - Reorders the list — **ranking is explicitly a human decision, not model judgment**
   - Sanity-checks `last_updated` / pricing / ratings for anything stale enough to need
     a refresh (staleness flagged at >30 days in the CLI, >60 days in the web UI)

   CLI: `nodes/human_review.py`, blocking terminal input; a rejection loops back to
   this same node for another pass at the selection (not back to the guardrail — see
   the callout in §2). Web: the Review screen, a live editable table with an
   include/exclude toggle, reorder buttons, and a final-count stepper per candidate —
   there's no separate approve/reject round trip in the browser, since the operator's
   edits *are* the review.
3. **Post-draft QA/humanize pass** — the brief's "QA to humanise the writing"
   requirement. Built as two pieces, deliberately lighter than a full reviewer
   workflow: **inline editing** on every section of the generated draft (title, meta
   description, intro, each company's summary/gaps, each FAQ item —
   `frontend/src/components/EditableText.tsx` / `EditableHtml.tsx`), which is the
   actual mechanism for a human to humanize the copy; and a **"Send for review"**
   button that's a client-side status marker only (a timestamp shown next to the
   button, cleared the moment the draft is edited or regenerated again) — no backend
   persistence, no reviewer role, no notification. A real review workflow (a second
   person picking this up, approving/rejecting with comments, a durable record of what
   was sent) is still not built.

---

## 6. What's built vs. what's still not built

This section was written when only the data layer existed. Nearly everything it once
listed as "designed, not yet coded" is now built — kept here (rewritten) so it's still
useful as a status check rather than misleading.

**Built — shared pipeline core** (`src/listicle_pipeline/`, used by both entry points):
- Scope guardrail LLM call (`nodes/guardrail.py`)
- Intent classification + confidence-check LLM call (`nodes/intent.py`)
- Deterministic Tools DB query (`db.py`, `nodes/db_query.py`)
- Live keyword generation — lexical / semantic / intent, 3 parallel LLM calls per
  request, exactly the prompts and temperatures designed in §4b (`nodes/keywords.py`)
- Retrieval merge (`nodes/retrieval_merge.py`)
- Summariser — per-company prose, one parallel LLM call per approved company via a
  dynamic LangGraph `Send` fan-out (`nodes/summariser.py`)
- Formatter — title/dek/intro, buying-criteria, and FAQ prose (3 parallel LLM calls),
  plus fully deterministic assembly of the comparison table and company sections that
  never trusts an LLM to reproduce a price or rating verbatim (`nodes/formatter.py`)

**Built — CLI** (`main.py`, `graph.py`): the full pipeline end-to-end in one process,
including the blocking-terminal HITL step, writing the finished draft to
`output/<slug>.json`.

**Built — web app** (`api/` + `frontend/`): a FastAPI backend implementing a 3-endpoint
REST contract, and a 5-screen React frontend with a fully interactive HITL review table,
inline draft editing, and automated SEO placement checks surfaced as pass/fail badges
(`api/seo_checks.py`) — the "automated SEO placement checks" this section used to list
as not-yet-built. See `docs/architecture.md` for exactly how this reuses the same core
node functions as the CLI without duplicating any pipeline logic.

**Still not built:**
- **Live Tavily / G2 API integration** — always explicitly scoped to a later phase
  (§3), and still is. Every run, CLI or web, uses only the synthetic dataset.
- **Decay-weighted default ranking** — still just a raw `days_since_update` field and a
  simple rating-descending sort; the `weight = e^(-days_since_update / half_life)`
  scoring design from §4a was never implemented.
- **Automated placement-check retry loop** — the SEO checks themselves run and are
  shown to the human (`api/seo_checks.py`), but a failing check doesn't automatically
  feed a targeted correction back into the formatter for regeneration; a human sees the
  red badge and decides what to do.
- **A real post-draft review workflow** — "Send for review" (§5, checkpoint 3) is a
  client-side status marker, not a durable record, a reviewer role, or a notification.
- **Company-level keyword personalization, review-text mining, multi-operator HITL
  conflict handling, and routable/shareable per-stage URLs** — all explicitly named as
  future scope when they came up (§7, and the frontend spec's own open questions) and
  none of them were built.

---

## 7. What breaks at scale / future scope

- **6 categories → 60 categories:** the closed-set classification approach (matching against a fixed list) stops being maintainable; would need embeddings or a proper classifier instead.
- **Review-level summarization:** currently only aggregate rating + count. Mining individual review text for themes is a real improvement but was cut for scope — G2/Capterra review scraping is blocked, and this would need the live G2 API.
- **Company-level keyword personalization:** keyword generation is category-level only for now. A future pass could generate lightweight per-company keyword variants (`"{company} pricing"`, `"{company} vs {competitor}"`) as part of the same live call, without needing a separate database.
- **Data freshness at scale:** with live retrieval (Tavily/G2 API) instead of a static synthetic DB, staleness handling becomes a real operational concern for the company data — the decay-weighted scoring design in §4a becomes necessary rather than optional.
- **Three live LLM calls per article request** for keyword generation is cheap at low request volume; at scale this is the pipeline's main latency and cost driver, since every request pays for fresh generation instead of a cache hit. Worth revisiting caching per (category, request-shape) if request volume grows, without going back to a single static precomputed table.
- **Schema depth / data enrichment:** the current DB schema (`positioning`, `starting_price`, `aggregated_rating`, `review_count`, `what_it_does_well`, `gaps`, `best_for`) only supports generic "what to look for" framing — pricing model, rating/review volume, a couple of strengths, a couple of limitations, who it's best for. It can't surface category-specific evaluation dimensions — e.g. for event registration/ticketing, things like branding depth, agenda personalization, push targeting, matchmaking, in-app engagement, onsite integration, CRM sync, or analytics export. Those aren't fields in the schema today; they'd have to be invented or forced out of the free-text `what_it_does_well`/`gaps` bullets, which isn't reliable. A future pass would need either category-specific structured fields (schema-per-category, harder to keep generic) or a richer enrichment step — pulling feature-level detail (plausibly via the Phase 2 Tavily integration) and tagging it against a per-category rubric of buyer-relevant dimensions, rather than relying on generic bullets to imply depth they don't have.
- **Video links / rich media:** no field currently captures demo videos, product walkthroughs, or embeddable media — the schema is text-and-numbers only. A future pass could add a `video_url` (or list of them) per company, sourced either manually or via live retrieval, to let the formatter embed a demo clip in that company's section rather than relying purely on prose.
- **Product personalization / featured placement:** there's no mechanism today to showcase a specific vendor (e.g. Company, if company is the requesting party) more prominently than a plain ranked entry — no "featured" flag, no boosted section treatment, no separate callout block in the formatter. A future pass would need an explicit, disclosed mechanism for this (e.g. a `featured: true` field plus formatter logic for a highlighted card/section) so any such boosting is a visible, auditable design choice rather than silently skewing the ranking that §5 defines as a human decision.
-**Compliance layer:** no compliance/legal review step exists in the pipeline today — e.g. checking competitor claims for accuracy before publish, disclosure requirements if any vendor gets featured/boosted placement, defamation risk in `gaps` bullets, trademark/logo usage for competitor names, or region-specific advertising/review regulations. This isn't designed yet because the underlying **business logic needs to come from stakeholders first** — what counts as an approved claim, what disclosure language is required, who signs off — before it can be turned into a pipeline stage (likely another HITL checkpoint, similar in shape to §5, rather than an automated check).
- **Real review summarization vs. aggregate-only:** today `aggregated_rating` and `review_count` are the only review signal — a single number and a count, no text. This is different from (and a prerequisite gap ahead of) the review-level mining idea above: before themes can be mined, the pipeline needs access to the actual review corpus per company (via live G2 API or another source) instead of a pre-aggregated score, since a synthetic DB has no raw reviews to summarize from in the first place.
- **Decay-weighted default ranking** — still just a raw `days_since_update` field and a
  simple rating-descending sort; the `weight = e^(-days_since_update / half_life)`
  scoring design from §4a was never implemented.
 
---

## 8. Files in this submission

```
Listicle Project/
├── README.md                    this document
├── docs/
│   ├── README.md                 architecture narrative — layers, shared core, how to run each piece
│   └── architecture.md           component diagram + full request-flow sequence diagram
├── data/
│   ├── synthetic_tool_db.csv     103 synthetic companies, 6 categories (§4a)
│   └── synthetic_tool_db.json    same data, JSON
├── src/listicle_pipeline/        shared pipeline core - see §6
│   ├── state.py                   every Pydantic model, used by every entry point
│   ├── db.py                      deterministic company lookup
│   ├── config.py                  env loading, LLM client factory
│   ├── graph.py                   the CLI's cyclic StateGraph
│   └── nodes/                     guardrail, intent, db_query, keywords, retrieval_merge,
│                                   human_review, summariser, formatter
├── main.py                       CLI entry point — `uv run python main.py`
├── api/                          FastAPI backend — `uv run uvicorn api.main:app`
│   ├── main.py                    the 3 REST endpoints
│   ├── retrieval_graph.py         cycle-free StateGraph reusing the shared retrieval nodes
│   ├── draft_graph.py             cycle-free StateGraph reusing the shared summariser/formatter nodes
│   ├── cache.py                   in-memory bridge for primary_keyword/keyword_set across calls
│   ├── mappers.py, seo_checks.py, faq_jsonld.py    deterministic response shaping
│   └── schemas.py                 the REST contract's request/response models
├── frontend/                     Vite + React + TypeScript web app — `npm run dev`
│   └── src/screens/, components/, state/    the 5 screens, inline editing, the reducer state machine
├── tests/                        pytest — deterministic unit tests (shared core + `api/`)
├── evals/                        evaluation framework — accuracy/precision/recall and groundedness
│   ├── datasets/                  golden test cases for guardrail/intent classification
│   └── results/                   timestamped eval run output
├── output/                       generated drafts, written by the CLI (gitignored)
└── pyproject.toml / uv.lock      Python dependencies
```
