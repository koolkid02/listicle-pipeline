from src.listicle_pipeline.nodes.formatter import _keywords, assemble_draft
from src.listicle_pipeline.state import (
    Company,
    CompanySummary,
    Keyword,
    PipelineState,
    RetrievalOutput,
    SummarySource,
    TitleDekBlock,
)


def _company(name: str, price: str, rating: float) -> Company:
    return Company(
        company_name=name,
        category="Project Management Software",
        positioning="Positioning",
        starting_price=price,
        aggregated_rating=rating,
        review_count=100,
        what_it_does_well=["Does well"],
        gaps=["Gap"],
        best_for="Small teams",
        website_url="https://example.com",
        source_url="https://example.com/pricing",
        last_updated="2026-08-01",
        days_since_update=10,
    )


def _summary(name: str) -> CompanySummary:
    return CompanySummary(
        company_name=name,
        summary_blurb=f"{name} is great.",
        does_well_prose=["It does well."],
        gaps_prose=["It has a gap."],
        best_for_line="Best for small teams.",
        pricing_line=f"From ${name}",
        rating_line="G2: 4.5/5",
        source=SummarySource(company_name=name, generated_at="2026-08-26T00:00:00Z"),
    )


def test_assemble_draft_preserves_final_companies_order():
    companies = [_company("Zeta", "$10/mo", 4.9), _company("Alpha", "$5/mo", 4.2)]
    # company_summaries deliberately in the OPPOSITE order, simulating parallel
    # Send-dispatched calls completing out of order.
    summaries = [_summary("Alpha"), _summary("Zeta")]

    state = PipelineState(
        user_prompt="x",
        final_companies=companies,
        company_summaries=summaries,
        title_dek=TitleDekBlock(
            title="Top Tools", url_slug="top-tools", dek="A dek.", intro_paragraphs=["p1", "p2"]
        ),
        buying_criteria_section=[],
        faq=[],
    )

    result = assemble_draft(state)
    draft = result["final_draft"]

    assert [row.company_name for row in draft.comparison_table.rows] == ["Zeta", "Alpha"]
    assert [s.company_name for s in draft.company_sections] == ["Zeta", "Alpha"]
    assert draft.comparison_table.rows[0].starting_price == "$10/mo"
    assert draft.comparison_table.rows[0].rating == 4.9


def test_assemble_draft_skips_company_without_summary():
    companies = [_company("Zeta", "$10/mo", 4.9), _company("Missing", "$1/mo", 3.0)]
    summaries = [_summary("Zeta")]

    state = PipelineState(
        user_prompt="x",
        final_companies=companies,
        company_summaries=summaries,
        title_dek=TitleDekBlock(title="T", url_slug="t", dek="d", intro_paragraphs=["p"]),
    )

    draft = assemble_draft(state)["final_draft"]
    assert len(draft.company_sections) == 1
    assert draft.company_sections[0].company_name == "Zeta"


def test_keywords_filters_by_type_and_stage():
    retrieval_output = RetrievalOutput(
        category="Project Management Software",
        primary_keyword="project management software",
        companies=[],
        keywords=[
            Keyword(keyword="pm tool", relationship_type="lexical", intent_stage="comparison", similarity_score=0.9),
            Keyword(
                keyword="what is pm software",
                relationship_type="intent",
                intent_stage="informational",
                similarity_score=0.8,
            ),
            Keyword(
                keyword="pm software pricing",
                relationship_type="intent",
                intent_stage="commercial_investigation",
                similarity_score=0.7,
            ),
        ],
    )

    assert _keywords(retrieval_output, "lexical") == ["pm tool"]
    assert _keywords(retrieval_output, "intent", "informational") == ["what is pm software"]
    assert _keywords(retrieval_output, "intent", "commercial_investigation") == ["pm software pricing"]
    assert _keywords(retrieval_output, "semantic") == []
