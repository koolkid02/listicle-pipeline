import pytest

from src.listicle_pipeline.nodes.keywords import keyword_intent, keyword_lexical, keyword_semantic
from src.listicle_pipeline.state import PipelineState

pytestmark = pytest.mark.llm_eval

# Deliberately a small subset (not the full intent dataset) - keyword generation has no
# single correct answer, so this only checks structural validity and the temp=0
# semantic branch's reproducibility, not correctness against a golden label.
CASES = [
    {"category": "Project Management Software", "primary_keyword": "project management software"},
    {"category": "Tax Filing Software", "primary_keyword": "tax filing software"},
]


@pytest.mark.parametrize("case", CASES, ids=[c["category"] for c in CASES])
def test_keyword_branches_return_valid_nonempty_lists(case, eval_callback_handler):
    state = PipelineState(user_prompt="x", category=case["category"], primary_keyword=case["primary_keyword"])

    with eval_callback_handler.label(f"keywords:{case['category']}"):
        lexical = keyword_lexical(state)["kw_lexical"]
        semantic = keyword_semantic(state)["kw_semantic"]
        intent = keyword_intent(state)["kw_intent"]

    for branch_name, keywords in [("lexical", lexical), ("semantic", semantic), ("intent", intent)]:
        assert keywords, f"{branch_name} returned no keywords for {case['category']}"
        assert all(k.keyword.strip() for k in keywords), f"{branch_name} returned an empty keyword string"


def test_semantic_branch_is_reproducible_at_temperature_zero(eval_callback_handler):
    state = PipelineState(
        user_prompt="x",
        category="Project Management Software",
        primary_keyword="project management software",
    )
    with eval_callback_handler.label("keywords:semantic-reproducibility"):
        first = {k.keyword for k in keyword_semantic(state)["kw_semantic"]}
        second = {k.keyword for k in keyword_semantic(state)["kw_semantic"]}

    assert first == second, f"temperature=0 semantic branch drifted between calls: {first} vs {second}"
