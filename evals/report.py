"""Builds and prints the aggregate eval report: accuracy/precision/recall for the
classification stages, groundedness pass rate for the generative stages, and
latency/token/error stats per stage from the observability log.

Usage:
    python -m evals.report <run_id>   # reload and print a past run's report, no API calls
"""

import json
import subprocess
import sys
from pathlib import Path

from src.listicle_pipeline.state import CATEGORIES

from . import observability
from .metrics import binary_confusion, multiclass_report

RESULTS_DIR = Path(__file__).parent / "results"
LOGS_DIR = RESULTS_DIR / "logs"


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def build_report(
    run_id: str,
    guardrail_results: list[tuple[bool, bool]],
    intent_results: list[tuple[str, str]],
    groundedness_results: list[tuple[str, bool, list[str]]],
    log_path: Path,
    placement_results: list[tuple[str, dict]] | None = None,
) -> dict:
    report: dict = {"run_id": run_id, "git_sha": _git_sha()}

    if guardrail_results:
        preds, labels = zip(*guardrail_results)
        report["guardrail"] = binary_confusion(list(preds), list(labels))

    if intent_results:
        preds, labels = zip(*intent_results)
        report["intent"] = multiclass_report(list(preds), list(labels), CATEGORIES)

    if groundedness_results:
        total = len(groundedness_results)
        passed = sum(1 for _, ok, _ in groundedness_results if ok)
        report["groundedness"] = {
            "n": total,
            "pass_rate": passed / total if total else 0.0,
            "failures": [
                {"case_id": cid, "violations": violations}
                for cid, ok, violations in groundedness_results
                if not ok
            ],
        }

    if placement_results:
        n = len(placement_results)
        lexical_in_title_rate = sum(1 for _, m in placement_results if m["lexical_in_title"]) / n
        lexical_in_first_100_words_rate = (
            sum(1 for _, m in placement_results if m["lexical_in_first_100_words"]) / n
        )
        total_semantic = sum(m["semantic_used"] + m["semantic_missing"] for _, m in placement_results)
        used_semantic = sum(m["semantic_used"] for _, m in placement_results)
        semantic_coverage = used_semantic / total_semantic if total_semantic else 0.0
        intent_in_faq_rate = sum(1 for _, m in placement_results if m["intent_terms_in_faq"] > 0) / n

        report["placement"] = {
            "n": n,
            "lexical_in_title_rate": lexical_in_title_rate,
            "lexical_in_first_100_words_rate": lexical_in_first_100_words_rate,
            "semantic_coverage": semantic_coverage,
            "intent_in_faq_rate": intent_in_faq_rate,
            "per_case": [{"case_id": cid, **metrics} for cid, metrics in placement_results],
        }

    log_entries = observability.read_log(log_path)
    report["observability"] = observability.summarize_log(log_entries)

    return report


def format_summary_table(report: dict) -> str:
    lines = [f"=== Eval report: run {report['run_id']} (commit {report['git_sha']}) ==="]

    if "guardrail" in report:
        g = report["guardrail"]
        lines.append(
            f"\nGuardrail (n={g['n']}): accuracy={g['accuracy']:.2f} "
            f"precision={g['precision']:.2f} recall={g['recall']:.2f} f1={g['f1']:.2f}"
        )

    if "intent" in report:
        i = report["intent"]
        lines.append(
            f"\nIntent (n={i['n']}): accuracy={i['accuracy']:.2f} "
            f"macro_precision={i['macro_precision']:.2f} macro_recall={i['macro_recall']:.2f} "
            f"macro_f1={i['macro_f1']:.2f}"
        )
        for cls, m in i["per_class"].items():
            lines.append(
                f"    {cls:<45} precision={m['precision']:.2f} recall={m['recall']:.2f} support={m['support']}"
            )

    if "groundedness" in report:
        gr = report["groundedness"]
        lines.append(f"\nGroundedness (n={gr['n']}): pass_rate={gr['pass_rate']:.2f}")
        for failure in gr["failures"]:
            lines.append(f"    FAIL {failure['case_id']}: {failure['violations']}")

    if "placement" in report:
        p = report["placement"]
        lines.append(
            f"\nPlacement (n={p['n']}): lexical_in_title={p['lexical_in_title_rate']:.2f} "
            f"lexical_in_first_100_words={p['lexical_in_first_100_words_rate']:.2f} "
            f"semantic_coverage={p['semantic_coverage']:.2f} "
            f"intent_in_faq={p['intent_in_faq_rate']:.2f}"
        )
        for case in p["per_case"]:
            lines.append(
                f"    {case['case_id']}: title={case['lexical_in_title']} "
                f"first100={case['lexical_in_first_100_words']} "
                f"semantic={case['semantic_used']}/{case['semantic_used'] + case['semantic_missing']} "
                f"intent_in_faq={case['intent_terms_in_faq']}"
            )

    if report.get("observability"):
        lines.append("\nObservability (per stage):")
        for stage, bucket in report["observability"].items():
            lines.append(
                f"    {stage:<20} calls={bucket['calls']:<4} errors={bucket['errors']:<3} "
                f"avg_latency_ms={bucket['avg_duration_ms']:.0f} total_tokens={bucket['total_tokens']}"
            )

    return "\n".join(lines)


def write_report(report: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{report['run_id']}-{report['git_sha']}.json"
    out_path.write_text(json.dumps(report, indent=2))
    return out_path


def load_report(run_id: str) -> dict:
    matches = sorted(RESULTS_DIR.glob(f"{run_id}-*.json"))
    if not matches:
        raise FileNotFoundError(f"No report found for run_id {run_id!r} in {RESULTS_DIR}")
    return json.loads(matches[-1].read_text())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m evals.report <run_id>")
        sys.exit(1)
    print(format_summary_table(load_report(sys.argv[1])))
