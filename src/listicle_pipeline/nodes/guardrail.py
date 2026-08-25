from pydantic import BaseModel

from ..config import TEMPERATURE_GUARDRAIL, get_llm, load_prompt
from ..state import PipelineState


class _ScopeDecision(BaseModel):
    in_scope: bool
    reason: str


def scope_guardrail(state: PipelineState) -> dict:
    llm = get_llm(TEMPERATURE_GUARDRAIL).with_structured_output(_ScopeDecision)
    prompt = load_prompt("scope_guardrail").format(user_prompt=state.user_prompt)
    decision: _ScopeDecision = llm.invoke(prompt)
    return {"in_scope": decision.in_scope, "scope_reason": decision.reason}


def clarify(state: PipelineState) -> dict:
    print(f"\nThat doesn't look like a listicle request: {state.scope_reason}")
    print("This pipeline only generates ranked SEO listicles comparing software companies in one category.")
    new_prompt = input("Please restate your request: ").strip()
    return {
        "user_prompt": new_prompt or state.user_prompt,
        "guardrail_attempts": state.guardrail_attempts + 1,
    }
