from pydantic import BaseModel

from ..config import TEMPERATURE_FORMATTER, get_llm, load_prompt
from ..state import (
    BuyingCriterionItem,
    CompanySection,
    ComparisonRow,
    ComparisonTable,
    FaqItem,
    FormatterDraft,
    PipelineState,
    RetrievalOutput,
    TitleDekBlock,
)

COMPARISON_TABLE_COLUMNS = ["Tool", "Best for", "Starting price", "G2 rating"]


def _keywords(retrieval_output: RetrievalOutput, relationship_type: str, intent_stage: str | None = None) -> list[str]:
    return [
        k.keyword
        for k in retrieval_output.keywords
        if k.relationship_type == relationship_type and (intent_stage is None or k.intent_stage == intent_stage)
    ]


class _BuyingCriteriaList(BaseModel):
    items: list[BuyingCriterionItem]


class _FaqList(BaseModel):
    items: list[FaqItem]


def formatter_title_dek(state: PipelineState) -> dict:
    retrieval_output = state.retrieval_output
    assert retrieval_output is not None

    llm = get_llm(TEMPERATURE_FORMATTER).with_structured_output(TitleDekBlock)
    prompt = load_prompt("formatter_title_dek").format(
        primary_keyword=state.primary_keyword,
        category=state.category,
        company_count=len(state.final_companies),
        lexical_keywords=", ".join(_keywords(retrieval_output, "lexical")),
        semantic_keywords=", ".join(_keywords(retrieval_output, "semantic")),
    )
    block: TitleDekBlock = llm.invoke(prompt)
    return {"title_dek": block}


def formatter_buying_criteria(state: PipelineState) -> dict:
    retrieval_output = state.retrieval_output
    assert retrieval_output is not None

    llm = get_llm(TEMPERATURE_FORMATTER).with_structured_output(_BuyingCriteriaList)
    prompt = load_prompt("formatter_buying_criteria").format(
        primary_keyword=state.primary_keyword,
        category=state.category,
        semantic_keywords=", ".join(_keywords(retrieval_output, "semantic")),
    )
    result: _BuyingCriteriaList = llm.invoke(prompt)
    return {"buying_criteria_section": result.items}


def formatter_faq(state: PipelineState) -> dict:
    retrieval_output = state.retrieval_output
    assert retrieval_output is not None

    informational = _keywords(retrieval_output, "intent", "informational")
    llm = get_llm(TEMPERATURE_FORMATTER).with_structured_output(_FaqList)
    prompt = load_prompt("formatter_faq").format(
        primary_keyword=state.primary_keyword,
        category=state.category,
        informational_keywords=", ".join(informational) if informational else "(none generated)",
    )
    result: _FaqList = llm.invoke(prompt)
    return {"faq": result.items}


def assemble_draft(state: PipelineState) -> dict:
    assert state.title_dek is not None

    summaries_by_name = {s.company_name: s for s in state.company_summaries}

    # Iterate final_companies (not company_summaries) to preserve the HITL-approved
    # order - Send-dispatched summarise_company calls run in parallel and can complete
    # in any order, so company_summaries order isn't guaranteed to match.
    rows = []
    company_sections = []
    for company in state.final_companies:
        summary = summaries_by_name.get(company.company_name)
        if summary is None:
            continue
        rows.append(
            ComparisonRow(
                company_name=summary.company_name,
                best_for_line=summary.best_for_line,
                starting_price=company.starting_price,
                rating=company.aggregated_rating,
            )
        )
        company_sections.append(
            CompanySection(
                company_name=summary.company_name,
                h3=summary.company_name,
                summary_blurb=summary.summary_blurb,
                does_well_prose=summary.does_well_prose,
                gaps_prose=summary.gaps_prose,
                pricing_line=summary.pricing_line,
                rating_line=summary.rating_line,
                best_for_line=summary.best_for_line,
            )
        )

    draft = FormatterDraft(
        title=state.title_dek.title,
        url_slug=state.title_dek.url_slug,
        dek=state.title_dek.dek,
        intro_paragraphs=state.title_dek.intro_paragraphs,
        comparison_table=ComparisonTable(columns=COMPARISON_TABLE_COLUMNS, rows=rows),
        company_sections=company_sections,
        buying_criteria_section=state.buying_criteria_section,
        faq=state.faq,
    )
    return {"final_draft": draft}
