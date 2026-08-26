# Architecture Diagram

Companion diagram to [`docs/README.md`](./README.md). Two views: the static component
layout, and the dynamic request flow for one full listicle generation.

---

## 1. Component overview

```mermaid
flowchart TB
    subgraph client["Clients"]
        cli["CLI\nmain.py"]
        browser["Browser\nfrontend/ (Vite + React)"]
    end

    subgraph frontend["Frontend — 5 screens + reducer"]
        direction TB
        screens["Request → Guardrail → Retrieval →\nReview (HITL) → Draft"]
        state["pipelineState.ts\n(useReducer state machine)"]
        editing["EditableText / EditableHtml\n(inline draft editing)"]
    end

    subgraph api["Backend API — api/ (FastAPI)"]
        direction TB
        endpoints["POST /pipeline/classify\nGET  /pipeline/retrieval\nPOST /pipeline/generate-draft"]
        rgraph["retrieval_graph.py\n(static 4-way fan-out)"]
        dgraph["draft_graph.py\n(dynamic Send fan-out)"]
        cache["cache.py\nin-memory: primary_keyword +\nkeyword_set per category_id"]
        shaping["mappers.py / seo_checks.py /\nfaq_jsonld.py\n(deterministic response shaping)"]
    end

    subgraph cligraph["CLI graph — src/listicle_pipeline/graph.py"]
        direction TB
        cyclenote["StateGraph with cycles:\nclarify / confirm / HITL-reject\nall re-enter at scope_guardrail"]
        hitl["human_review\n(blocking terminal input())"]
    end

    subgraph core["Shared pipeline core — src/listicle_pipeline/"]
        direction TB
        nodes["nodes/\nguardrail · intent · db_query ·\nkeywords · retrieval_merge ·\nsummariser · formatter"]
        models["state.py\nPydantic models shared by\nevery entry point"]
    end

    subgraph data["Data & external services"]
        direction TB
        db[("data/synthetic_tool_db.csv\n103 companies, 6 categories")]
        openai(["OpenAI API\nguardrail / intent / 3× keyword gen /\nsummariser / 3× formatter"])
    end

    cli --> cligraph
    cligraph --> nodes

    browser --> screens --> state
    state --> editing
    screens -->|"HTTP/JSON"| endpoints
    endpoints --> cache
    endpoints --> rgraph
    endpoints --> dgraph
    endpoints --> shaping
    rgraph --> nodes
    dgraph --> nodes

    nodes --> models
    nodes --> db
    nodes --> openai

    style hitl fill:#4a3510,stroke:#f0a83a,color:#f0d9a8
    style editing fill:#4a3510,stroke:#f0a83a,color:#f0d9a8
    style core fill:#0f2a28,stroke:#49c7b8,color:#bdf0e8
```

**Reading the colors:** amber-outlined boxes (`human_review`, inline editing) are the
human-decision points — everything else is deterministic or LLM-automated. This mirrors
the teal/amber convention already used in the frontend's pipeline rail
(`frontend/src/components/PipelineRail.tsx`).

**The one fact this diagram exists to make obvious:** `api/retrieval_graph.py` and
`api/draft_graph.py` do not reimplement any pipeline logic. They import the exact same
node functions from `src/listicle_pipeline/nodes/` that the CLI's `graph.py` uses, and
wire them into small, purpose-built `StateGraph`s that fit the API's stateless
request/response shape (no cycles, no blocking terminal I/O). The CLI and the API are
two different *orchestrations* of one shared core, not two implementations.

---

## 2. Request flow — one full listicle, browser path

```mermaid
sequenceDiagram
    actor Op as Operator
    participant FE as Frontend
    participant API as api/main.py
    participant Cache as cache.py
    participant RG as retrieval_graph
    participant DG as draft_graph
    participant Nodes as shared nodes/
    participant LLM as OpenAI

    Op->>FE: types request / picks category chip
    FE->>API: POST /pipeline/classify
    API->>Nodes: scope_guardrail()
    Nodes->>LLM: classify scope
    API->>Nodes: intent_confidence()
    Nodes->>LLM: classify category + confidence
    API->>Cache: store primary_keyword by category_id
    API-->>FE: scope_ok, category, confidence, blocked

    FE->>API: GET /pipeline/retrieval?category_id=...
    API->>Cache: read primary_keyword
    API->>RG: invoke(category, primary_keyword)
    par 4-way fan-out (one superstep)
        RG->>Nodes: tools_db_query()
        RG->>Nodes: keyword_lexical()
        RG->>Nodes: keyword_semantic()
        RG->>Nodes: keyword_intent()
    end
    Nodes->>LLM: 3× keyword generation
    RG->>Nodes: retrieval_merge()
    API->>Cache: store RetrievalOutput
    API-->>FE: tools[] + keyword_set

    Op->>FE: include/exclude, reorder, set final count (HITL)
    FE->>API: POST /pipeline/generate-draft
    API->>Cache: read RetrievalOutput + primary_keyword
    API->>DG: invoke(final_companies)
    DG->>Nodes: Send fan-out → summarise_company() × N
    Nodes->>LLM: N parallel summarise calls
    par 3-way fan-out (one superstep)
        DG->>Nodes: formatter_title_dek()
        DG->>Nodes: formatter_buying_criteria()
        DG->>Nodes: formatter_faq()
    end
    Nodes->>LLM: 3× formatter generation
    DG->>Nodes: assemble_draft() [deterministic, no LLM]
    API-->>FE: title, sections[], faq[], seo_checks, faq_schema_jsonld

    Op->>FE: inline-edit title/sections/FAQ, "Send for review"
    Note over FE: edits + send-status are client-side only,<br/>held in the reducer, never round-tripped
```

**The CLI path** runs the same `scope_guardrail` → `intent_confidence` →
[`tools_db_query` ∥ 3× `keyword_*`] → `retrieval_merge` sequence, but then hits
`human_review` — a real blocking `input()` call in the terminal — instead of returning
to a client. Rejecting at that step re-enters at `scope_guardrail` (same node, capped
retries), which is the "every failure routes back to one re-entry point" principle from
the original design README. Once approved, it continues through the identical
`summarise_company` → formatter fan-out → `assemble_draft` sequence and writes
`output/<slug>.json`.
