# Architecture

This document explains how the pieces of this project fit together. For the visual
diagrams (component overview + request-flow sequence), see
[`docs/architecture.md`](./architecture.md).

## What this is

An SEO listicle generation pipeline (Zuddl take-home) with two entry points into the
same core: a CLI (`main.py`) and a browser UI (`frontend/`, backed by `api/`). Both
turn a keyword request into a ranked, human-reviewed, SEO-formatted comparison article
— they just differ in how the human-review checkpoint and the request/response
boundary work.

## The four layers

### 1. Shared pipeline core — `src/listicle_pipeline/`

Every piece of actual pipeline logic lives here, as plain, reusable functions — not
tied to the CLI or the API:

| File | Responsibility |
|---|---|
| `state.py` | Every Pydantic model in the system: `Company`, `Keyword`, `RetrievalOutput`, `CompanySummary`, `FormatterDraft`, and the LangGraph `PipelineState` schema. |
| `db.py` | Deterministic company lookup by category from `data/synthetic_tool_db.csv` — no LLM involved. |
| `nodes/guardrail.py`, `nodes/intent.py` | Scope classification and category/confidence classification — both pure functions, no I/O, safe to call from a stateless API handler. |
| `nodes/db_query.py`, `nodes/keywords.py` | The retrieval fan-out: one deterministic DB query, three parallel LLM keyword-generation calls (lexical/semantic/intent). |
| `nodes/retrieval_merge.py` | Joins the fan-out into one `RetrievalOutput`. |
| `nodes/human_review.py` | The CLI's interactive terminal checkpoint — the **only** node in this package that isn't reused by the API, since the API's HITL step happens entirely client-side instead. |
| `nodes/summariser.py` | Per-company prose generation, dispatched as a dynamic LangGraph `Send` fan-out (one parallel call per approved company). |
| `nodes/formatter.py` | Three parallel prose calls (title/dek/intro, buying-criteria, FAQ) plus a fully deterministic `assemble_draft` that copies verified prices/ratings/summaries into the final draft — never trusts an LLM to reproduce structured data verbatim. |
| `graph.py` | The CLI's `StateGraph`: wires all of the above into one pipeline with real cycles (`clarify`/`confirm`/HITL-reject all re-enter at `scope_guardrail`) and a bounded retry cap per cycle. |

### 2. CLI — `main.py`

Runs `graph.py` end-to-end in one process: prompts for a request, drives the human
through `clarify`/`confirm`/`human_review` via blocking terminal `input()`, and writes
the finished `FormatterDraft` to `output/<slug>.json`.

```bash
uv run python main.py
```

### 3. Backend API — `api/`

A FastAPI app implementing the 3-endpoint contract from the frontend spec
(`POST /pipeline/classify`, `GET /pipeline/retrieval`, `POST /pipeline/generate-draft`).
It does not reuse `graph.py` — that graph has cycles and a blocking terminal node,
neither of which fit a stateless HTTP handler. Instead:

| File | Responsibility |
|---|---|
| `retrieval_graph.py` | A small standalone `StateGraph`: the same static 4-way fan-out (`tools_db_query` + 3× `keyword_*`) → `retrieval_merge`, with no cycles. |
| `draft_graph.py` | A small standalone `StateGraph`: `Send` fan-out to `summarise_company` → the 3 formatter branches → `assemble_draft`. |
| `cache.py` | In-memory, single-process dict bridging `primary_keyword` and the generated `keyword_set` across the three calls, since the documented request contract doesn't carry them forward on its own. Sized for a single-operator internal tool, not multi-tenant scale. |
| `mappers.py`, `seo_checks.py`, `faq_jsonld.py` | Deterministic, LLM-free response shaping: internal models → the contract's JSON shapes, keyword-placement scoring (word-overlap matching against a keyword's significant words, not exact-phrase), and `schema.org` FAQPage JSON-LD. |
| `main.py` | The 3 routes, CORS, and orchestration between the pieces above. |

```bash
uv run uvicorn api.main:app --port 8000
```

### 4. Frontend — `frontend/`

Vite + React + TypeScript. Five screens driven by one `useReducer` state machine
(`src/state/pipelineState.ts`), matching the backend's 5 conceptual stages:

1. **Request** — a single freeform request field, or a category chip that skips
   classification entirely.
2. **Guardrail & intent** — confidence bar; a manual category picker when confidence is
   too low.
3. **Retrieval** — read-only view of the matched companies and generated keywords.
4. **Human review** — the real HITL screen: include/exclude, reorder, set a final
   count, staleness flags.
5. **Draft** — the generated article, with click-to-edit on every section
   (`components/EditableText.tsx`, `components/EditableHtml.tsx`), a client-side "Send
   for review" status marker, SEO check badges, and Copy as Text/HTML.

```bash
cd frontend && npm run dev
```

## Design principles carried through every layer

- **One core, two orchestrations.** No pipeline logic is duplicated between the CLI and
  the API — see `docs/architecture.md` §1 for exactly which files are shared.
- **LLM for prose, code for data.** Anything that must reproduce a verified fact
  (price, rating, a company name) is assembled deterministically in Python
  (`assemble_draft`, the comparison table, `mappers.py`). LLM calls are reserved for
  genuinely generative prose.
- **One human-decision checkpoint per surface.** The CLI's `human_review` and the
  frontend's Review screen are the only points where the pipeline defers to a person
  instead of a model — visually marked amber throughout (`PipelineRail.tsx`, the
  diagram above) against teal for everything automated.
- **Every failure re-enters at one place.** In the CLI graph, an off-scope request, a
  low-confidence category match, and a HITL rejection all loop back to the same
  `scope_guardrail`/`human_review` re-entry points with a bounded retry cap, rather than
  each having its own dead end.
