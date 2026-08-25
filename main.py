import sys
import uuid

from src.listicle_pipeline.config import RECURSION_LIMIT
from src.listicle_pipeline.graph import build_graph
from src.listicle_pipeline.state import PipelineState


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip() or input(
        "What listicle would you like to generate? "
    ).strip()

    graph = build_graph()
    config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "recursion_limit": RECURSION_LIMIT,
    }

    final_state = graph.invoke(PipelineState(user_prompt=prompt), config=config)

    if not final_state.get("hitl_approved"):
        print("\nNo approved retrieval output was produced.")
        return

    output = final_state["retrieval_output"]
    print(f"\n=== Retrieval output: {output.category} ===")
    print(f"Primary keyword: {output.primary_keyword}")
    print(f"\nApproved companies ({len(final_state['final_companies'])}):")
    for c in final_state["final_companies"]:
        print(f"  - {c.company_name} ({c.aggregated_rating}/5, {c.review_count} reviews)")
    print(f"\nGenerated keywords ({len(output.keywords)}):")
    for k in output.keywords:
        print(f"  [{k.relationship_type}/{k.intent_stage}] {k.keyword} ({k.similarity_score:.2f})")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n\nNo input received - exiting.")
