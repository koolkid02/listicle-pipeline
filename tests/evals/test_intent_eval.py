import json
from pathlib import Path

import pytest

from evals import collector
from src.listicle_pipeline.nodes.intent import intent_confidence
from src.listicle_pipeline.state import PipelineState

pytestmark = pytest.mark.llm_eval

CASES = json.loads((Path(__file__).parents[2] / "evals/datasets/intent_cases.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=[c["prompt"][:40] for c in CASES])
def test_intent_case(case, eval_callback_handler):
    with eval_callback_handler.label(f"intent:{case['prompt'][:30]}"):
        result = intent_confidence(PipelineState(user_prompt=case["prompt"]))

    collector.intent_results.append((result["category"], case["expected_category"]))
    assert result["category"] == case["expected_category"], (
        f"got {result['category']!r} (confidence={result['confidence']:.2f}), "
        f"expected {case['expected_category']!r}"
    )
