from langgraph.graph import END, START, StateGraph

from src.listicle_pipeline.nodes.db_query import tools_db_query
from src.listicle_pipeline.nodes.keywords import keyword_intent, keyword_lexical, keyword_semantic
from src.listicle_pipeline.nodes.retrieval_merge import retrieval_merge
from src.listicle_pipeline.state import PipelineState

BRANCHES = ["tools_db_query", "keyword_lexical", "keyword_semantic", "keyword_intent"]


def build_retrieval_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("tools_db_query", tools_db_query)
    graph.add_node("keyword_lexical", keyword_lexical)
    graph.add_node("keyword_semantic", keyword_semantic)
    graph.add_node("keyword_intent", keyword_intent)
    graph.add_node("retrieval_merge", retrieval_merge)

    for branch in BRANCHES:
        graph.add_edge(START, branch)
        graph.add_edge(branch, "retrieval_merge")
    graph.add_edge("retrieval_merge", END)

    return graph.compile()
