from pydantic import BaseModel

from ..config import (
    TEMPERATURE_INTENT,
    TEMPERATURE_LEXICAL,
    TEMPERATURE_SEMANTIC,
    get_llm,
    load_prompt,
)
from ..state import Keyword, PipelineState


class _KeywordList(BaseModel):
    keywords: list[Keyword]


def _generate(state: PipelineState, prompt_name: str, temperature: float) -> list[Keyword]:
    llm = get_llm(temperature).with_structured_output(_KeywordList)
    prompt = load_prompt(prompt_name).format(
        category=state.category, primary_keyword=state.primary_keyword
    )
    try:
        result: _KeywordList = llm.invoke(prompt)
        return result.keywords
    except Exception as exc:  # noqa: BLE001 - one branch failing must not sink retrieval_merge
        print(f"\n[warning] {prompt_name} keyword generation failed: {exc}")
        return []


def keyword_lexical(state: PipelineState) -> dict:
    return {"kw_lexical": _generate(state, "keyword_lexical", TEMPERATURE_LEXICAL)}


def keyword_semantic(state: PipelineState) -> dict:
    return {"kw_semantic": _generate(state, "keyword_semantic", TEMPERATURE_SEMANTIC)}


def keyword_intent(state: PipelineState) -> dict:
    return {"kw_intent": _generate(state, "keyword_intent", TEMPERATURE_INTENT)}
