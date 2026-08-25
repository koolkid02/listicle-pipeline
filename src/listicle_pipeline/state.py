import operator
from typing import Annotated, Literal, Optional

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


class SummarySource(BaseModel):
    company_name: str
    generated_at: str


class CompanySummary(BaseModel):
    company_name: str
    summary_blurb: str
    does_well_prose: list[str]
    gaps_prose: list[str]
    best_for_line: str
    pricing_line: str
    rating_line: str
    source: SummarySource


class TitleDekBlock(BaseModel):
    title: str
    url_slug: str
    dek: str
    intro_paragraphs: list[str]


class BuyingCriterionItem(BaseModel):
    h3: str
    body: str


class FaqItem(BaseModel):
    question: str
    answer: str


class ComparisonRow(BaseModel):
    company_name: str
    best_for_line: str
    starting_price: str
    rating: float


class ComparisonTable(BaseModel):
    columns: list[str]
    rows: list[ComparisonRow]


class CompanySection(BaseModel):
    company_name: str
    h3: str
    summary_blurb: str
    does_well_prose: list[str]
    gaps_prose: list[str]
    pricing_line: str
    rating_line: str
    best_for_line: str


class FormatterDraft(BaseModel):
    title: str
    url_slug: str
    dek: str
    intro_paragraphs: list[str]
    comparison_table: ComparisonTable
    company_sections: list[CompanySection]
    buying_criteria_section: list[BuyingCriterionItem]
    faq: list[FaqItem]


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
    hitl_attempts: int = 0

    company_summaries: Annotated[list[CompanySummary], operator.add] = Field(default_factory=list)
    title_dek: Optional[TitleDekBlock] = None
    buying_criteria_section: list[BuyingCriterionItem] = Field(default_factory=list)
    faq: list[FaqItem] = Field(default_factory=list)
    final_draft: Optional[FormatterDraft] = None
