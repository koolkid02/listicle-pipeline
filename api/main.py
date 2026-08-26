from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.listicle_pipeline.config import CONFIDENCE_THRESHOLD
from src.listicle_pipeline.nodes.guardrail import scope_guardrail
from src.listicle_pipeline.nodes.intent import intent_confidence
from src.listicle_pipeline.state import Company, PipelineState

from . import cache
from .categories import CATEGORY_ID_MAP, CATEGORY_NAME_TO_ID, available_categories
from .draft_graph import build_draft_graph
from .mappers import (
    map_category,
    map_confidence,
    map_generate_draft_response,
    map_retrieval_response,
    slugify,
)
from .retrieval_graph import build_retrieval_graph
from .schemas import (
    CategoryOut,
    ClassifyRequest,
    ClassifyResponse,
    GenerateDraftRequest,
    GenerateDraftResponse,
    RetrievalResponse,
)

app = FastAPI(title="Listicle Console API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_retrieval_graph = build_retrieval_graph()
_draft_graph = build_draft_graph()


def _available_categories() -> list[CategoryOut]:
    return [CategoryOut(**c) for c in available_categories()]


@app.post("/pipeline/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest) -> ClassifyResponse:
    if req.manual_category_id:
        if req.manual_category_id not in CATEGORY_ID_MAP:
            raise HTTPException(status_code=400, detail="Unknown manual_category_id")
        category_name = CATEGORY_ID_MAP[req.manual_category_id]
        primary_keyword = req.primary_keyword or category_name
        cache.set_primary_keyword(req.manual_category_id, primary_keyword)
        return ClassifyResponse(
            scope_ok=True,
            category=map_category(category_name),
            confidence=100,
            blocked=False,
            available_categories=_available_categories(),
        )

    prompt = f"write a listicle about {req.primary_keyword}"
    if req.secondary_keyword:
        prompt += f" and {req.secondary_keyword}"

    state = PipelineState(user_prompt=prompt)
    guardrail_result = scope_guardrail(state)

    if not guardrail_result["in_scope"]:
        return ClassifyResponse(
            scope_ok=False,
            category=None,
            confidence=0,
            blocked=True,
            available_categories=_available_categories(),
            reason=guardrail_result["scope_reason"],
        )

    state = state.model_copy(update=guardrail_result)
    intent_result = intent_confidence(state)

    category_name = intent_result["category"]
    category_id = CATEGORY_NAME_TO_ID[category_name]
    primary_keyword = req.primary_keyword or intent_result["primary_keyword"]
    blocked = intent_result["confidence"] < CONFIDENCE_THRESHOLD

    cache.set_primary_keyword(category_id, primary_keyword)

    return ClassifyResponse(
        scope_ok=True,
        category=map_category(category_name),
        confidence=map_confidence(intent_result["confidence"]),
        blocked=blocked,
        available_categories=_available_categories(),
    )


@app.get("/pipeline/retrieval", response_model=RetrievalResponse)
def retrieval(category_id: str) -> RetrievalResponse:
    if category_id not in CATEGORY_ID_MAP:
        raise HTTPException(status_code=400, detail="Unknown category_id")
    category_name = CATEGORY_ID_MAP[category_id]

    cached = cache.get(category_id)
    primary_keyword = cached["primary_keyword"] if cached else category_name

    state = PipelineState(user_prompt="", category=category_name, primary_keyword=primary_keyword)
    result = _retrieval_graph.invoke(state)
    retrieval_output = result["retrieval_output"]

    cache.set_retrieval_output(category_id, retrieval_output)

    return map_retrieval_response(retrieval_output)


@app.post("/pipeline/generate-draft", response_model=GenerateDraftResponse)
def generate_draft(req: GenerateDraftRequest) -> GenerateDraftResponse:
    if req.category_id not in CATEGORY_ID_MAP:
        raise HTTPException(status_code=400, detail="Unknown category_id")

    cached = cache.get(req.category_id)
    if cached is None or cached["retrieval_output"] is None:
        raise HTTPException(
            status_code=409,
            detail="No retrieval result cached for this category - call GET /pipeline/retrieval first",
        )

    retrieval_output = cached["retrieval_output"]
    primary_keyword = cached["primary_keyword"]

    companies_by_id = {slugify(c.company_name): c for c in retrieval_output.companies}
    final_companies: list[Company] = []
    for tool_id in req.selected_tool_ids_in_order:
        company = companies_by_id.get(tool_id)
        if company is None:
            raise HTTPException(status_code=400, detail=f"Unknown tool id: {tool_id}")
        final_companies.append(company)
    if req.final_count:
        final_companies = final_companies[: req.final_count]

    state = PipelineState(
        user_prompt="",
        category=retrieval_output.category,
        primary_keyword=primary_keyword,
        retrieval_output=retrieval_output,
        final_companies=final_companies,
    )
    result = _draft_graph.invoke(state)
    draft = result["final_draft"]

    return map_generate_draft_response(draft, final_companies, retrieval_output)
