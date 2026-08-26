from src.listicle_pipeline.state import FormatterDraft, RetrievalOutput

from .schemas import KeywordPlacementsOut, SeoChecksOut


def _keywords(retrieval_output: RetrievalOutput, relationship_type: str) -> list[str]:
    return [k.keyword for k in retrieval_output.keywords if k.relationship_type == relationship_type]


def _word_count(draft: FormatterDraft) -> int:
    text_blocks = list(draft.intro_paragraphs)
    for section in draft.company_sections:
        text_blocks.append(section.summary_blurb)
        text_blocks.extend(section.does_well_prose)
        text_blocks.extend(section.gaps_prose)
        text_blocks.append(section.best_for_line)
    for item in draft.buying_criteria_section:
        text_blocks.append(item.body)
    for item in draft.faq:
        text_blocks.append(item.answer)
    return sum(len(block.split()) for block in text_blocks)


def compute_seo_checks(draft: FormatterDraft, retrieval_output: RetrievalOutput) -> SeoChecksOut:
    lexical = _keywords(retrieval_output, "lexical")
    semantic = _keywords(retrieval_output, "semantic")
    intent_informational = [
        k.keyword
        for k in retrieval_output.keywords
        if k.relationship_type == "intent" and k.intent_stage == "informational"
    ]

    title_lower = draft.title.lower()
    first_100_words = " ".join(" ".join(draft.intro_paragraphs).split()[:100]).lower()

    lexical_in_title = any(kw.lower() in title_lower for kw in lexical)
    lexical_in_first_100_words = any(kw.lower() in first_100_words for kw in lexical)

    prose_pool = " ".join(
        draft.intro_paragraphs
        + [item.body for item in draft.buying_criteria_section]
        + [s.summary_blurb for s in draft.company_sections]
    ).lower()
    semantic_used = [kw for kw in semantic if kw.lower() in prose_pool]
    semantic_missing = [kw for kw in semantic if kw.lower() not in prose_pool]

    faq_text = " ".join(f"{item.question} {item.answer}" for item in draft.faq).lower()
    intent_terms_in_faq = sum(1 for kw in intent_informational if kw.lower() in faq_text)

    return SeoChecksOut(
        word_count=_word_count(draft),
        heading_structure_valid=True,
        keyword_placements=KeywordPlacementsOut(
            lexical_in_title=lexical_in_title,
            lexical_in_first_100_words=lexical_in_first_100_words,
            semantic_terms_used=semantic_used,
            semantic_terms_missing=semantic_missing,
            intent_terms_in_faq=intent_terms_in_faq,
        ),
    )
