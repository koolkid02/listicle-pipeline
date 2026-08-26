from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from src.listicle_pipeline.nodes.formatter import (
    assemble_draft,
    formatter_buying_criteria,
    formatter_faq,
    formatter_title_dek,
)
from src.listicle_pipeline.nodes.summariser import summarise_company
from src.listicle_pipeline.state import PipelineState

FORMATTER_BRANCHES = ["formatter_title_dek", "formatter_buying_criteria", "formatter_faq"]


def _dispatch_summaries(state: PipelineState) -> list[Send]:
    return [
        Send("summarise_company", {"company": c, "primary_keyword": state.primary_keyword})
        for c in state.final_companies
    ]


def build_draft_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("summarise_company", summarise_company)
    graph.add_node("formatter_title_dek", formatter_title_dek)
    graph.add_node("formatter_buying_criteria", formatter_buying_criteria)
    graph.add_node("formatter_faq", formatter_faq)
    graph.add_node("assemble_draft", assemble_draft)

    graph.add_conditional_edges(START, _dispatch_summaries)

    for branch in FORMATTER_BRANCHES:
        graph.add_edge("summarise_company", branch)
        graph.add_edge(branch, "assemble_draft")
    graph.add_edge("assemble_draft", END)

    return graph.compile()
