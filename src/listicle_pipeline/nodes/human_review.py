from ..config import MAX_HITL_ATTEMPTS
from ..state import Company, PipelineState

STALE_DAYS_THRESHOLD = 30


def _parse_selection(raw: str, n: int) -> list[int]:
    raw = raw.strip().lower()
    if raw in ("", "all"):
        return list(range(n))
    indices: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            indices.extend(range(int(start) - 1, int(end)))
        elif part:
            indices.append(int(part) - 1)
    return [i for i in indices if 0 <= i < n]


def _print_table(companies: list[Company]) -> None:
    print(f"\nCandidate companies ({len(companies)}):")
    for i, c in enumerate(companies, start=1):
        stale = " ⚠ STALE" if c.days_since_update > STALE_DAYS_THRESHOLD else ""
        print(
            f"  [{i:>2}] {c.company_name:<20} rating={c.aggregated_rating:<4} "
            f"reviews={c.review_count:<6} price={c.starting_price:<20} "
            f"updated {c.days_since_update}d ago{stale}"
        )


def human_review(state: PipelineState) -> dict:
    assert state.retrieval_output is not None
    retrieval_output = state.retrieval_output

    companies = sorted(
        retrieval_output.companies, key=lambda c: c.aggregated_rating, reverse=True
    )
    _print_table(companies)

    print("\nTop keywords generated:")
    for rel in ("lexical", "semantic", "intent"):
        top = [k.keyword for k in retrieval_output.keywords if k.relationship_type == rel][:3]
        print(f"  {rel}: {', '.join(top) if top else '(none generated)'}")

    print(
        "\nEnter the indices to include, in your preferred final order "
        "(e.g. '3,1,7' or '1-8'), or 'all' to keep every candidate in the order shown."
    )
    while True:
        raw = input("Include (default: all): ")
        try:
            selected_indices = _parse_selection(raw, len(companies))
            break
        except ValueError:
            print(f"Couldn't parse '{raw}' - use indices/ranges like '3,1,7' or '1-8', or 'all'.")
    final_companies = [companies[i] for i in selected_indices]

    print(f"\nSelected {len(final_companies)} companies:")
    for c in final_companies:
        print(f"  - {c.company_name}")

    approve_raw = input("\nApprove this list and continue? [Y/n]: ").strip().lower()
    approved = approve_raw in ("", "y", "yes")

    if not approved:
        print(
            f"\nNo problem - let's redo the selection "
            f"(attempt {state.hitl_attempts + 1}/{MAX_HITL_ATTEMPTS})."
        )
        return {"hitl_approved": False, "hitl_attempts": state.hitl_attempts + 1}

    return {
        "hitl_approved": True,
        "final_companies": final_companies,
        "final_count": len(final_companies),
    }
