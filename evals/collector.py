"""In-memory accumulator for one pytest session's eval results. Test modules append to
these lists as parametrized cases run; tests/evals/conftest.py's pytest_sessionfinish
hook reads them to build the aggregate report."""

guardrail_results: list[tuple[bool, bool]] = []  # (predicted_in_scope, expected_in_scope)
intent_results: list[tuple[str, str]] = []  # (predicted_category, expected_category)
groundedness_results: list[tuple[str, bool, list[str]]] = []  # (case_id, ok, violations)
placement_results: list[tuple[str, dict]] = []  # (case_id, keyword-placement signals)


def reset() -> None:
    guardrail_results.clear()
    intent_results.clear()
    groundedness_results.clear()
    placement_results.clear()
