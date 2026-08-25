import json
import sys
import uuid

from src.listicle_pipeline.config import OUTPUT_DIR, RECURSION_LIMIT
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

    draft = final_state.get("final_draft")
    if draft is None:
        print("\nNo draft was produced.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{draft.url_slug}.json"
    out_path.write_text(json.dumps(draft.model_dump(), indent=2))

    print(f"\n=== {draft.title} ===")
    print(draft.dek)
    print(f"\nCompanies covered: {len(draft.company_sections)}")
    print(f"Buying-criteria items: {len(draft.buying_criteria_section)}")
    print(f"FAQ entries: {len(draft.faq)}")
    print(f"\nFull draft written to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n\nNo input received - exiting.")
