import pytest

from api.draft_graph import build_draft_graph
from api.seo_checks import compute_seo_checks
from evals import collector
from evals.fixtures import FORMATTER_CASES, sample_retrieval_output
from src.listicle_pipeline.state import PipelineState

pytestmark = pytest.mark.llm_eval

_draft_graph = build_draft_graph()


def _run_draft(case: dict):
    retrieval_output = sample_retrieval_output(case["category"], case["primary_keyword"], case["n"])
    state = PipelineState(
        user_prompt="x",
        category=case["category"],
        primary_keyword=case["primary_keyword"],
        retrieval_output=retrieval_output,
        final_companies=retrieval_output.companies,
    )
    result = _draft_graph.invoke(state)
    return result["final_draft"], retrieval_output


@pytest.mark.parametrize("case", FORMATTER_CASES, ids=[c["primary_keyword"] for c in FORMATTER_CASES])
def test_placement_checks(case, eval_callback_handler):
    with eval_callback_handler.label(f"placement:{case['primary_keyword']}"):
        draft, retrieval_output = _run_draft(case)

    checks = compute_seo_checks(draft, retrieval_output)
    p = checks.keyword_placements
    collector.placement_results.append(
        (
            case["primary_keyword"],
            {
                "lexical_in_title": p.lexical_in_title,
                "lexical_in_first_100_words": p.lexical_in_first_100_words,
                "semantic_used": len(p.semantic_terms_used),
                "semantic_missing": len(p.semantic_terms_missing),
                "intent_terms_in_faq": p.intent_terms_in_faq,
            },
        )
    )
    # Soft eval - keyword placement is a quality signal with normal run-to-run
    # variance, not a correctness contract like groundedness. This measures and
    # reports; it doesn't gate the test run on any single case.
