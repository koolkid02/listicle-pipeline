import time

import pytest

from evals import collector
from evals.observability import JSONLCallbackHandler
from evals.report import LOGS_DIR, build_report, format_summary_table, write_report
from src.listicle_pipeline import config

RUN_ID = time.strftime("%Y%m%d-%H%M%S")
LOG_PATH = LOGS_DIR / f"{RUN_ID}.jsonl"


@pytest.fixture(scope="session", autouse=True)
def eval_callback_handler():
    """Session-scoped: only actually does anything when a test in tests/evals/ is
    selected to run (i.e. `pytest -m llm_eval`) - a plain `pytest` run deselects every
    test here before fixture setup, so this never fires and costs nothing."""
    collector.reset()
    handler = JSONLCallbackHandler(LOG_PATH)
    with config.use_callbacks([handler]):
        yield handler


def pytest_sessionfinish(session, exitstatus):
    if not (collector.guardrail_results or collector.intent_results or collector.groundedness_results):
        return
    report = build_report(
        run_id=RUN_ID,
        guardrail_results=collector.guardrail_results,
        intent_results=collector.intent_results,
        groundedness_results=collector.groundedness_results,
        log_path=LOG_PATH,
    )
    print("\n" + format_summary_table(report))
    out_path = write_report(report)
    print(f"\nFull report written to {out_path}")
