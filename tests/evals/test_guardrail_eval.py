import json
from pathlib import Path

import pytest

from evals import collector
from src.listicle_pipeline.nodes.guardrail import scope_guardrail
from src.listicle_pipeline.state import PipelineState

pytestmark = pytest.mark.llm_eval

CASES = json.loads((Path(__file__).parents[2] / "evals/datasets/guardrail_cases.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=[c["prompt"][:40] for c in CASES])
def test_guardrail_case(case, eval_callback_handler):
    with eval_callback_handler.label(f"guardrail:{case['prompt'][:30]}"):
        result = scope_guardrail(PipelineState(user_prompt=case["prompt"]))

    collector.guardrail_results.append((result["in_scope"], case["expected_in_scope"]))
    assert result["in_scope"] == case["expected_in_scope"], result["scope_reason"]
