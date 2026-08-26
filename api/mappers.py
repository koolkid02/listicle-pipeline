import html
import re

from src.listicle_pipeline.state import Company, CompanySection, FormatterDraft, Keyword, RetrievalOutput

from .categories import CATEGORY_NAME_TO_ID
from .faq_jsonld import build_faq_jsonld
from .schemas import (
    CategoryOut,
    FaqOut,
    GenerateDraftResponse,
    IntentKeywordOut,
    KeywordSetOut,
    RetrievalResponse,
    SectionOut,
    SemanticKeywordOut,
    ToolOut,
)
from .seo_checks import compute_seo_checks


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def map_category(category_name: str) -> CategoryOut:
    return CategoryOut(id=CATEGORY_NAME_TO_ID[category_name], name=category_name)


def map_confidence(confidence: float) -> int:
    return round(confidence * 100)


def map_tool(company: Company) -> ToolOut:
    return ToolOut(
        id=slugify(company.company_name),
        company_name=company.company_name,
        positioning=company.positioning,
        starting_price=company.starting_price,
        aggregated_rating=company.aggregated_rating,
        review_count=company.review_count,
        what_it_does_well=company.what_it_does_well,
        gaps=company.gaps,
        best_for=company.best_for,
        website_url=company.website_url,
        source_url=company.source_url,
        last_updated=company.last_updated,
        days_since_update=company.days_since_update,
    )


def map_keywords(keywords: list[Keyword]) -> KeywordSetOut:
    return KeywordSetOut(
        lexical=[k.keyword for k in keywords if k.relationship_type == "lexical"],
        semantic=[
            SemanticKeywordOut(term=k.keyword, similarity_score=k.similarity_score)
            for k in keywords
            if k.relationship_type == "semantic"
        ],
        intent=[
            IntentKeywordOut(term=k.keyword, stage=k.intent_stage)
            for k in keywords
            if k.relationship_type == "intent"
        ],
    )


def map_retrieval_response(retrieval_output: RetrievalOutput) -> RetrievalResponse:
    return RetrievalResponse(
        tools=[map_tool(c) for c in retrieval_output.companies],
        keywords=map_keywords(retrieval_output.keywords),
    )


def _p(text: str) -> str:
    return f"<p>{html.escape(text)}</p>"


def _ul(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{html.escape(i)}</li>" for i in items) + "</ul>"


def build_lede_html(intro_paragraphs: list[str]) -> str:
    return "".join(_p(p) for p in intro_paragraphs)


def build_body_html(section: CompanySection) -> str:
    parts = [_p(section.summary_blurb)]
    if section.does_well_prose:
        parts.append(_ul(section.does_well_prose))
    parts.append(_p(f"{section.pricing_line} · {section.rating_line}"))
    parts.append(_p(section.best_for_line))
    return "".join(parts)


def build_gaps_html(section: CompanySection) -> str:
    return _ul(section.gaps_prose) if section.gaps_prose else ""


def map_generate_draft_response(
    draft: FormatterDraft, final_companies: list[Company], retrieval_output: RetrievalOutput
) -> GenerateDraftResponse:
    company_by_name = {c.company_name: c for c in final_companies}

    sections = []
    for rank, section in enumerate(draft.company_sections, start=1):
        company = company_by_name.get(section.company_name)
        sections.append(
            SectionOut(
                rank=rank,
                tool_id=slugify(section.company_name),
                company_name=section.company_name,
                website_url=company.website_url if company else "",
                source_url=company.source_url if company else "",
                body_html=build_body_html(section),
                gaps_html=build_gaps_html(section),
            )
        )

    return GenerateDraftResponse(
        title=draft.title,
        slug=draft.url_slug,
        meta_description=draft.dek,
        lede_html=build_lede_html(draft.intro_paragraphs),
        sections=sections,
        faq=[FaqOut(question=f.question, answer=f.answer) for f in draft.faq],
        faq_schema_jsonld=build_faq_jsonld(draft.faq),
        seo_checks=compute_seo_checks(draft, retrieval_output),
    )


__all__ = [
    "slugify",
    "map_category",
    "map_confidence",
    "map_tool",
    "map_keywords",
    "map_retrieval_response",
    "build_lede_html",
    "build_body_html",
    "build_gaps_html",
    "map_generate_draft_response",
]
