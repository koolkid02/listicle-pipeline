import pytest

from evals import collector
from evals.fixtures import SUMMARISER_CASES, sample_companies
from evals.groundedness import check_summary_groundedness
from src.listicle_pipeline.nodes.summariser import summarise_company

pytestmark = pytest.mark.llm_eval

CASES = [
    (case["category"], case["primary_keyword"], company)
    for case in SUMMARISER_CASES
    for company in sample_companies(case["category"], case["n"])
]


@pytest.mark.parametrize(
    "category,primary_keyword,company", CASES, ids=[c[2].company_name for c in CASES]
)
def test_summary_groundedness(category, primary_keyword, company, eval_callback_handler):
    with eval_callback_handler.label(f"summariser:{company.company_name}"):
        result = summarise_company({"company": company, "primary_keyword": primary_keyword})

    summary = result["company_summaries"][0]
    groundedness = check_summary_groundedness(company, summary)

    collector.groundedness_results.append(
        (f"summariser:{company.company_name}", groundedness.ok, groundedness.violations)
    )
    assert groundedness.ok, groundedness.violations
