from typing import Literal, Optional

from pydantic import BaseModel, Field

CATEGORIES = [
    "Project Management Software",
    "Hiring and HR Software",
    "Event Registration and Ticketing Software",
    "End-to-End CRM Software",
    "Tax Filing Software",
    "Email Marketing Software",
]

RelationshipType = Literal["lexical", "semantic", "intent"]
IntentStage = Literal["informational", "commercial_investigation", "comparison"]


class Company(BaseModel):
    company_name: str
    category: str
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


class Keyword(BaseModel):
    keyword: str
    relationship_type: RelationshipType
    intent_stage: IntentStage
    similarity_score: float


class RetrievalOutput(BaseModel):
    category: str
    primary_keyword: str
    companies: list[Company]
    keywords: list[Keyword]


class PipelineState(BaseModel):
    user_prompt: str

    in_scope: Optional[bool] = None
    scope_reason: Optional[str] = None

    category: Optional[str] = None
    primary_keyword: Optional[str] = None
    confidence: Optional[float] = None

    guardrail_attempts: int = 0

    db_companies: list[Company] = Field(default_factory=list)
    kw_lexical: list[Keyword] = Field(default_factory=list)
    kw_semantic: list[Keyword] = Field(default_factory=list)
    kw_intent: list[Keyword] = Field(default_factory=list)

    retrieval_output: Optional[RetrievalOutput] = None

    final_companies: list[Company] = Field(default_factory=list)
    final_count: Optional[int] = None
    hitl_approved: Optional[bool] = None
