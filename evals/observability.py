"""Local, file-based observability - no external account (LangSmith or otherwise)
needed. Logs one JSON line per LLM call (label, latency, token usage, errors) so
evals/report.py can surface cost/latency/error-rate alongside the accuracy and
groundedness numbers for the same run."""

import json
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from langchain_core.callbacks import BaseCallbackHandler


class JSONLCallbackHandler(BaseCallbackHandler):
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._starts: dict[uuid.UUID, float] = {}
        self._current_label = "unlabeled"

    @contextmanager
    def label(self, name: str):
        previous = self._current_label
        self._current_label = name
        try:
            yield
        finally:
            self._current_label = previous

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        self._starts[run_id] = time.monotonic()

    def on_llm_start(self, serialized, prompts, *, run_id, **kwargs):
        self._starts[run_id] = time.monotonic()

    def on_llm_end(self, response, *, run_id, **kwargs):
        self._write_entry(run_id, response=response, error=None)

    def on_llm_error(self, error, *, run_id, **kwargs):
        self._write_entry(run_id, response=None, error=str(error))

    def _write_entry(self, run_id, response, error):
        start = self._starts.pop(run_id, None)
        duration_ms = (time.monotonic() - start) * 1000 if start is not None else None

        token_usage = {}
        model_name = None
        if response is not None and response.llm_output:
            token_usage = response.llm_output.get("token_usage", {}) or {}
            model_name = response.llm_output.get("model_name")

        entry = {
            "label": self._current_label,
            "run_id": str(run_id),
            "duration_ms": duration_ms,
            "model": model_name,
            "token_usage": token_usage,
            "error": error,
        }
        with self.log_path.open("a") as f:
            f.write(json.dumps(entry) + "\n")


def read_log(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    with log_path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def summarize_log(entries: list[dict]) -> dict:
    """Aggregate per-label-prefix (the part before ':') latency/token/error stats."""
    by_stage: dict[str, dict] = {}
    for entry in entries:
        stage = entry["label"].split(":", 1)[0]
        bucket = by_stage.setdefault(
            stage, {"calls": 0, "errors": 0, "total_duration_ms": 0.0, "total_tokens": 0}
        )
        bucket["calls"] += 1
        if entry["error"]:
            bucket["errors"] += 1
        if entry["duration_ms"] is not None:
            bucket["total_duration_ms"] += entry["duration_ms"]
        bucket["total_tokens"] += (entry["token_usage"] or {}).get("total_tokens", 0)

    for stage, bucket in by_stage.items():
        bucket["avg_duration_ms"] = bucket["total_duration_ms"] / bucket["calls"] if bucket["calls"] else 0.0

    return by_stage
