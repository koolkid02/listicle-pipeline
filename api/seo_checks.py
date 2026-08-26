import re

from src.listicle_pipeline.state import FormatterDraft, RetrievalOutput

from .schemas import KeywordPlacementsOut, SeoChecksOut

_STOPWORDS = {
    "a", "an", "the", "for", "and", "or", "of", "in", "to", "with", "vs", "your",
    # generic listicle filler present in nearly every keyword and every title -
    # counting these would make the check trivially easy rather than meaningful.
    "best", "top",
}


def _significant_words(phrase: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", phrase.lower()) if w not in _STOPWORDS}


def _text_words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _keyword_present(keyword: str, text_words: set[str]) -> bool:
    significant = _significant_words(keyword)
    if not significant:
        return False
    overlap = significant & text_words
    threshold = -(-len(significant) // 2)  # ceil(n / 2), at least 1
    return len(overlap) >= threshold


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

    title_words = _text_words(draft.title)
    first_100_words = _text_words(" ".join(" ".join(draft.intro_paragraphs).split()[:100]))

    lexical_in_title = any(_keyword_present(kw, title_words) for kw in lexical)
    lexical_in_first_100_words = any(_keyword_present(kw, first_100_words) for kw in lexical)

    prose_pool = _text_words(
        " ".join(
            draft.intro_paragraphs
            + [item.body for item in draft.buying_criteria_section]
            + [s.summary_blurb for s in draft.company_sections]
        )
    )
    semantic_used = [kw for kw in semantic if _keyword_present(kw, prose_pool)]
    semantic_missing = [kw for kw in semantic if not _keyword_present(kw, prose_pool)]

    faq_words = _text_words(" ".join(f"{item.question} {item.answer}" for item in draft.faq))
    intent_terms_in_faq = sum(1 for kw in intent_informational if _keyword_present(kw, faq_words))

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
