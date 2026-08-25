from ..state import PipelineState, RetrievalOutput


def retrieval_merge(state: PipelineState) -> dict:
    all_keywords = [*state.kw_lexical, *state.kw_semantic, *state.kw_intent]
    retrieval_output = RetrievalOutput(
        category=state.category,
        primary_keyword=state.primary_keyword,
        companies=state.db_companies,
        keywords=all_keywords,
    )
    return {"retrieval_output": retrieval_output}
