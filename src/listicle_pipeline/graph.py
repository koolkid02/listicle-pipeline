from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Send

from .config import CONFIDENCE_THRESHOLD, MAX_GUARDRAIL_ATTEMPTS, MAX_HITL_ATTEMPTS
from .nodes.db_query import tools_db_query
from .nodes.formatter import (
    assemble_draft,
    formatter_buying_criteria,
    formatter_faq,
    formatter_title_dek,
)
from .nodes.guardrail import clarify, scope_guardrail
from .nodes.human_review import human_review
from .nodes.intent import confirm, intent_confidence
from .nodes.keywords import keyword_intent, keyword_lexical, keyword_semantic
from .nodes.retrieval_merge import retrieval_merge
from .nodes.summariser import summarise_company
from .state import PipelineState

KEYWORD_BRANCHES = ["tools_db_query", "keyword_lexical", "keyword_semantic", "keyword_intent"]
FORMATTER_BRANCHES = ["formatter_title_dek", "formatter_buying_criteria", "formatter_faq"]


def give_up(state: PipelineState) -> dict:
    if state.guardrail_attempts >= MAX_GUARDRAIL_ATTEMPTS:
        print(
            f"\nGiving up after {state.guardrail_attempts} attempts - "
            "the request still isn't resolving to an in-scope, high-confidence listicle task."
        )
    else:
        print(
            f"\nGiving up after {state.hitl_attempts} review attempts - "
            "no company selection was approved."
        )
    return {}


def route_after_guardrail(state: PipelineState) -> str:
    if state.in_scope:
        return "intent_confidence"
    if state.guardrail_attempts >= MAX_GUARDRAIL_ATTEMPTS:
        return "give_up"
    return "clarify"


def route_after_intent(state: PipelineState) -> str | list[str]:
    if state.confidence is not None and state.confidence >= CONFIDENCE_THRESHOLD:
        return KEYWORD_BRANCHES
    if state.guardrail_attempts >= MAX_GUARDRAIL_ATTEMPTS:
        return "give_up"
    return "confirm"


def route_after_review(state: PipelineState) -> str | list[Send]:
    if state.hitl_approved:
        # Map: one parallel Send per approved company. Reduced back into
        # PipelineState.company_summaries via its operator.add reducer.
        return [
            Send("summarise_company", {"company": c, "primary_keyword": state.primary_keyword})
            for c in state.final_companies
        ]
    if state.hitl_attempts >= MAX_HITL_ATTEMPTS:
        return "give_up"
    return "human_review"


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("scope_guardrail", scope_guardrail)
    graph.add_node("clarify", clarify)
    graph.add_node("intent_confidence", intent_confidence)
    graph.add_node("confirm", confirm)
    graph.add_node("tools_db_query", tools_db_query)
    graph.add_node("keyword_lexical", keyword_lexical)
    graph.add_node("keyword_semantic", keyword_semantic)
    graph.add_node("keyword_intent", keyword_intent)
    graph.add_node("retrieval_merge", retrieval_merge)
    graph.add_node("human_review", human_review)
    graph.add_node("give_up", give_up)
    graph.add_node("summarise_company", summarise_company)
    graph.add_node("formatter_title_dek", formatter_title_dek)
    graph.add_node("formatter_buying_criteria", formatter_buying_criteria)
    graph.add_node("formatter_faq", formatter_faq)
    graph.add_node("assemble_draft", assemble_draft)

    graph.set_entry_point("scope_guardrail")

    graph.add_conditional_edges(
        "scope_guardrail",
        route_after_guardrail,
        {"intent_confidence": "intent_confidence", "clarify": "clarify", "give_up": "give_up"},
    )
    graph.add_edge("clarify", "scope_guardrail")

    graph.add_conditional_edges(
        "intent_confidence",
        route_after_intent,
        {
            "tools_db_query": "tools_db_query",
            "keyword_lexical": "keyword_lexical",
            "keyword_semantic": "keyword_semantic",
            "keyword_intent": "keyword_intent",
            "confirm": "confirm",
            "give_up": "give_up",
        },
    )
    graph.add_edge("confirm", "scope_guardrail")

    for branch in KEYWORD_BRANCHES:
        graph.add_edge(branch, "retrieval_merge")
    graph.add_edge("retrieval_merge", "human_review")

    graph.add_conditional_edges(
        "human_review", route_after_review, {"give_up": "give_up", "human_review": "human_review"}
    )

    for branch in FORMATTER_BRANCHES:
        graph.add_edge("summarise_company", branch)
        graph.add_edge(branch, "assemble_draft")
    graph.add_edge("assemble_draft", END)

    graph.add_edge("give_up", END)

    return graph.compile(checkpointer=MemorySaver())
