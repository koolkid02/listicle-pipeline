from api.faq_jsonld import build_faq_jsonld
from api.mappers import (
    build_body_html,
    build_gaps_html,
    build_lede_html,
    map_category,
    map_confidence,
    map_generate_draft_response,
    map_keywords,
    map_retrieval_response,
    slugify,
)
from api.seo_checks import _keyword_present, _text_words, compute_seo_checks
from src.listicle_pipeline.state import (
    Company,
    CompanySection,
    ComparisonRow,
    ComparisonTable,
    FaqItem,
    FormatterDraft,
    Keyword,
    RetrievalOutput,
)


def _company(name: str) -> Company:
    return Company(
        company_name=name,
        category="Project Management Software",
        positioning="Positioning",
        starting_price="$10/mo",
        aggregated_rating=4.5,
        review_count=100,
        what_it_does_well=["Does well"],
        gaps=["Has a gap"],
        best_for="Small teams",
        website_url=f"https://{slugify(name)}.com",
        source_url=f"https://{slugify(name)}.com/pricing",
        last_updated="2026-08-01",
        days_since_update=10,
    )


def _section(name: str) -> CompanySection:
    return CompanySection(
        company_name=name,
        h3=name,
        summary_blurb=f"{name} is great.",
        does_well_prose=["It does well at X."],
        gaps_prose=["It has a gap in Y."],
        pricing_line="From $10/mo",
        rating_line="G2: 4.5/5",
        best_for_line="Best for small teams.",
    )


def _keyword(kw: str, rel: str, stage: str = "informational", score: float = 0.8) -> Keyword:
    return Keyword(keyword=kw, relationship_type=rel, intent_stage=stage, similarity_score=score)


def test_slugify():
    assert slugify("TaskForge") == "taskforge"
    assert slugify("Sparkline Mail") == "sparkline-mail"
    assert slugify("A & B, Inc.") == "a-b-inc"


def test_map_category():
    out = map_category("Project Management Software")
    assert out.id == "project-management"
    assert out.name == "Project Management Software"


def test_map_confidence():
    assert map_confidence(0.7) == 70
    assert map_confidence(0.955) == 96


def test_map_keywords_groups_by_relationship_type():
    keywords = [
        _keyword("pm tool", "lexical"),
        _keyword("resource allocation", "semantic", score=0.6),
        _keyword("what is pm software", "intent", stage="informational"),
    ]
    out = map_keywords(keywords)
    assert out.lexical == ["pm tool"]
    assert out.semantic[0].term == "resource allocation"
    assert out.semantic[0].similarity_score == 0.6
    assert out.intent[0].term == "what is pm software"
    assert out.intent[0].stage == "informational"


def test_map_retrieval_response():
    retrieval_output = RetrievalOutput(
        category="Project Management Software",
        primary_keyword="project management software",
        companies=[_company("TaskForge")],
        keywords=[_keyword("pm tool", "lexical")],
    )
    out = map_retrieval_response(retrieval_output)
    assert out.tools[0].id == "taskforge"
    assert out.tools[0].website_url == "https://taskforge.com"
    assert out.keywords.lexical == ["pm tool"]


def test_html_builders_escape_and_wrap():
    lede = build_lede_html(["Hello <script>alert(1)</script>", "Second paragraph"])
    assert "<script>" not in lede
    assert "&lt;script&gt;" in lede
    assert lede.count("<p>") == 2

    section = _section("TaskForge")
    body = build_body_html(section)
    assert "<ul><li>It does well at X.</li></ul>" in body
    assert "From $10/mo" in body

    gaps = build_gaps_html(section)
    assert gaps == "<ul><li>It has a gap in Y.</li></ul>"


def test_map_generate_draft_response_preserves_order_and_links():
    companies = [_company("Zeta"), _company("Alpha")]
    draft = FormatterDraft(
        title="Top Tools",
        url_slug="top-tools",
        dek="A dek.",
        intro_paragraphs=["p1", "p2"],
        comparison_table=ComparisonTable(
            columns=["Tool"],
            rows=[
                ComparisonRow(company_name="Zeta", best_for_line="x", starting_price="$1", rating=4.0),
                ComparisonRow(company_name="Alpha", best_for_line="y", starting_price="$2", rating=4.5),
            ],
        ),
        company_sections=[_section("Zeta"), _section("Alpha")],
        buying_criteria_section=[],
        faq=[FaqItem(question="Q1", answer="A1")],
    )
    retrieval_output = RetrievalOutput(
        category="Project Management Software",
        primary_keyword="project management software",
        companies=companies,
        keywords=[],
    )

    response = map_generate_draft_response(draft, companies, retrieval_output)

    assert [s.rank for s in response.sections] == [1, 2]
    assert [s.company_name for s in response.sections] == ["Zeta", "Alpha"]
    assert response.sections[0].website_url == "https://zeta.com"
    assert response.meta_description == "A dek."
    assert response.slug == "top-tools"
    assert response.faq_schema_jsonld["@type"] == "FAQPage"
    assert len(response.faq_schema_jsonld["mainEntity"]) == 1


def test_build_faq_jsonld_shape():
    jsonld = build_faq_jsonld([FaqItem(question="Q?", answer="A.")])
    assert jsonld["@context"] == "https://schema.org"
    assert jsonld["mainEntity"][0]["@type"] == "Question"
    assert jsonld["mainEntity"][0]["name"] == "Q?"
    assert jsonld["mainEntity"][0]["acceptedAnswer"]["text"] == "A."


def test_compute_seo_checks_detects_placement():
    retrieval_output = RetrievalOutput(
        category="Project Management Software",
        primary_keyword="project management software",
        companies=[],
        keywords=[
            _keyword("best project tools", "lexical"),
            _keyword("resource allocation", "semantic"),
            _keyword("missing semantic term", "semantic"),
            _keyword("what is pm software", "intent", stage="informational"),
        ],
    )
    draft = FormatterDraft(
        title="Best Project Tools of 2026",
        url_slug="best-project-tools",
        dek="d",
        intro_paragraphs=["The best project tools rely on strong resource allocation practices."],
        comparison_table=ComparisonTable(columns=[], rows=[]),
        company_sections=[],
        buying_criteria_section=[],
        faq=[FaqItem(question="What is pm software?", answer="It's software.")],
    )

    checks = compute_seo_checks(draft, retrieval_output)

    assert checks.keyword_placements.lexical_in_title is True
    assert checks.keyword_placements.lexical_in_first_100_words is True
    assert "resource allocation" in checks.keyword_placements.semantic_terms_used
    assert "missing semantic term" in checks.keyword_placements.semantic_terms_missing
    assert checks.keyword_placements.intent_terms_in_faq == 1
    assert checks.heading_structure_valid is True
    assert checks.word_count > 0


def test_keyword_present_matches_paraphrased_wording():
    # "best email marketing software" paraphrased as "the best email marketing
    # tools" - shares "email"/"marketing" (>= half of the significant words) but not
    # the exact phrase or "software". Real generated prose paraphrases like this
    # constantly, so exact substring matching used to fail nearly every draft.
    text_words = _text_words("The best email marketing tools available today.")
    assert _keyword_present("best email marketing software", text_words) is True


def test_keyword_present_rejects_incidental_overlap():
    # Only "software" overlaps (one word, below the ceil(n/2) threshold for a
    # 4-significant-word phrase) - genuinely unrelated text should still fail.
    text_words = _text_words("This tax software helps you file returns quickly.")
    assert _keyword_present("best email marketing software", text_words) is False
