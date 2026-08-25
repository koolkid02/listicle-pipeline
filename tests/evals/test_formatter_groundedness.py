import pytest

from evals import collector
from evals.fixtures import ALL_COMPANY_NAMES, FORMATTER_CASES, sample_retrieval_output
from evals.groundedness import (
    check_buying_criteria_groundedness,
    check_faq_groundedness,
    check_title_dek_company_count,
)
from src.listicle_pipeline.nodes.formatter import (
    formatter_buying_criteria,
    formatter_faq,
    formatter_title_dek,
)
from src.listicle_pipeline.state import PipelineState

pytestmark = pytest.mark.llm_eval


def _state(case: dict) -> PipelineState:
    retrieval_output = sample_retrieval_output(case["category"], case["primary_keyword"], case["n"])
    return PipelineState(
        user_prompt="x",
        category=case["category"],
        primary_keyword=case["primary_keyword"],
        retrieval_output=retrieval_output,
        final_companies=retrieval_output.companies,
    )


@pytest.mark.parametrize("case", FORMATTER_CASES, ids=[c["primary_keyword"] for c in FORMATTER_CASES])
def test_title_dek_company_count(case, eval_callback_handler):
    state = _state(case)
    with eval_callback_handler.label(f"formatter_title_dek:{case['primary_keyword']}"):
        result = formatter_title_dek(state)

    groundedness = check_title_dek_company_count(result["title_dek"], len(state.final_companies))
    collector.groundedness_results.append(
        (f"formatter_title_dek:{case['primary_keyword']}", groundedness.ok, groundedness.violations)
    )
    assert groundedness.ok, groundedness.violations


@pytest.mark.parametrize("case", FORMATTER_CASES, ids=[c["primary_keyword"] for c in FORMATTER_CASES])
def test_buying_criteria_groundedness(case, eval_callback_handler):
    state = _state(case)
    with eval_callback_handler.label(f"formatter_buying_criteria:{case['primary_keyword']}"):
        result = formatter_buying_criteria(state)

    groundedness = check_buying_criteria_groundedness(result["buying_criteria_section"], ALL_COMPANY_NAMES)
    collector.groundedness_results.append(
        (f"formatter_buying_criteria:{case['primary_keyword']}", groundedness.ok, groundedness.violations)
    )
    assert groundedness.ok, groundedness.violations


@pytest.mark.parametrize("case", FORMATTER_CASES, ids=[c["primary_keyword"] for c in FORMATTER_CASES])
def test_faq_groundedness(case, eval_callback_handler):
    state = _state(case)
    with eval_callback_handler.label(f"formatter_faq:{case['primary_keyword']}"):
        result = formatter_faq(state)

    groundedness = check_faq_groundedness(result["faq"], ALL_COMPANY_NAMES)
    collector.groundedness_results.append(
        (f"formatter_faq:{case['primary_keyword']}", groundedness.ok, groundedness.violations)
    )
    assert groundedness.ok, groundedness.violations
