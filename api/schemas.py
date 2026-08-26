from typing import Optional

from pydantic import BaseModel

# --- 3.1 POST /pipeline/classify ---


class ClassifyRequest(BaseModel):
    primary_keyword: str
    secondary_keyword: Optional[str] = None
    manual_category_id: Optional[str] = None


class CategoryOut(BaseModel):
    id: str
    name: str


class ClassifyResponse(BaseModel):
    scope_ok: bool
    category: Optional[CategoryOut]
    confidence: int
    blocked: bool
    available_categories: list[CategoryOut]
    reason: Optional[str] = None


# --- 3.2 GET /pipeline/retrieval ---


class ToolOut(BaseModel):
    id: str
    company_name: str
    positioning: str
    starting_price: str
    aggregated_rating: float
    review_count: int
    what_it_does_well: list[str]
    gaps: list[str]
    best_for: str
    website_url: str
    source_url: str
    last_updated: str
    days_since_update: int


class SemanticKeywordOut(BaseModel):
    term: str
    similarity_score: float


class IntentKeywordOut(BaseModel):
    term: str
    stage: str


class KeywordSetOut(BaseModel):
    lexical: list[str]
    semantic: list[SemanticKeywordOut]
    intent: list[IntentKeywordOut]


class RetrievalResponse(BaseModel):
    tools: list[ToolOut]
    keywords: KeywordSetOut


# --- 3.3 POST /pipeline/generate-draft ---


class GenerateDraftRequest(BaseModel):
    category_id: str
    selected_tool_ids_in_order: list[str]
    final_count: int


class SectionOut(BaseModel):
    rank: int
    tool_id: str
    company_name: str
    website_url: str
    source_url: str
    body_html: str
    gaps_html: str


class FaqOut(BaseModel):
    question: str
    answer: str


class KeywordPlacementsOut(BaseModel):
    lexical_in_title: bool
    lexical_in_first_100_words: bool
    semantic_terms_used: list[str]
    semantic_terms_missing: list[str]
    intent_terms_in_faq: int


class SeoChecksOut(BaseModel):
    word_count: int
    heading_structure_valid: bool
    keyword_placements: KeywordPlacementsOut


class GenerateDraftResponse(BaseModel):
    title: str
    slug: str
    meta_description: str
    lede_html: str
    sections: list[SectionOut]
    faq: list[FaqOut]
    faq_schema_jsonld: dict
    seo_checks: SeoChecksOut
