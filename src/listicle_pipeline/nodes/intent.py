from typing import Literal

from pydantic import BaseModel

from ..config import TEMPERATURE_GUARDRAIL, get_llm, load_prompt
from ..state import CATEGORIES, PipelineState


class _IntentClassification(BaseModel):
    category: Literal[tuple(CATEGORIES)]
    primary_keyword: str
    confidence: float


def intent_confidence(state: PipelineState) -> dict:
    llm = get_llm(TEMPERATURE_GUARDRAIL).with_structured_output(_IntentClassification)
    prompt = load_prompt("intent_confidence").format(
        categories="\n".join(f"- {c}" for c in CATEGORIES),
        user_prompt=state.user_prompt,
    )
    result: _IntentClassification = llm.invoke(prompt)
    return {
        "category": result.category,
        "primary_keyword": result.primary_keyword,
        "confidence": result.confidence,
    }


def confirm(state: PipelineState) -> dict:
    print(f"\nLow-confidence category match ({state.confidence:.2f}): '{state.category}'")
    print(f"Detected primary keyword: '{state.primary_keyword}'")
    print("Please restate your request more specifically (e.g. name the category explicitly).")
    new_prompt = input("Restate your request: ").strip()
    return {
        "user_prompt": new_prompt or state.user_prompt,
        "guardrail_attempts": state.guardrail_attempts + 1,
    }
