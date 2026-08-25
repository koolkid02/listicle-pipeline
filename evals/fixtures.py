"""Shared fixtures for groundedness eval tests - pulled from the real synthetic DB so
tests exercise realistic data shapes without hand-maintaining duplicate fixtures."""

from src.listicle_pipeline import db
from src.listicle_pipeline.state import Company, Keyword, RetrievalOutput

ALL_COMPANY_NAMES: list[str] = [c.company_name for c in db._load_all_companies()]


def sample_companies(category: str, n: int) -> list[Company]:
    companies = db.query_by_category(category)
    return companies[:n]


def sample_retrieval_output(category: str, primary_keyword: str, n_companies: int) -> RetrievalOutput:
    companies = sample_companies(category, n_companies)
    keywords = [
        Keyword(keyword=f"{primary_keyword} tool", relationship_type="lexical", intent_stage="comparison", similarity_score=0.9),
        Keyword(keyword=f"{primary_keyword} alternatives", relationship_type="semantic", intent_stage="comparison", similarity_score=0.8),
        Keyword(keyword=f"what is {primary_keyword}", relationship_type="intent", intent_stage="informational", similarity_score=0.85),
    ]
    return RetrievalOutput(
        category=category,
        primary_keyword=primary_keyword,
        companies=companies,
        keywords=keywords,
    )


SUMMARISER_CASES = [
    {"category": "Project Management Software", "primary_keyword": "project management software", "n": 2},
    {"category": "End-to-End CRM Software", "primary_keyword": "crm software", "n": 1},
]

FORMATTER_CASES = [
    {"category": "Hiring and HR Software", "primary_keyword": "hiring software", "n": 5},
    {"category": "Email Marketing Software", "primary_keyword": "email marketing software", "n": 3},
]
