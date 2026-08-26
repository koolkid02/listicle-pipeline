import type { Dispatch } from "react";
import { generateDraft } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { StalenessBadge } from "../components/StalenessBadge";
import { useAsyncAction } from "../lib/useAsyncAction";
import type { PipelineAction, PipelineState } from "../state/pipelineState";
import styles from "./ReviewScreen.module.css";

export function ReviewScreen({
  state,
  dispatch,
}: {
  state: PipelineState;
  dispatch: Dispatch<PipelineAction>;
}) {
  const draftAction = useAsyncAction(generateDraft);
  const data = state.retrieval;
  if (!data || !state.selectedCategoryId) return null;

  const toolsById = Object.fromEntries(data.tools.map((t) => [t.id, t]));
  const includedSet = new Set(state.includedToolIds);
  const excludedIds = data.tools.map((t) => t.id).filter((id) => !includedSet.has(id));
  const orderedIds = [...state.includedToolIds, ...excludedIds];

  function toggleInclude(id: string) {
    const next = includedSet.has(id)
      ? state.includedToolIds.filter((x) => x !== id)
      : [...state.includedToolIds, id];
    dispatch({ type: "SET_SELECTION", toolIds: next });
  }

  function move(id: string, delta: number) {
    const idx = state.includedToolIds.indexOf(id);
    const target = idx + delta;
    if (idx === -1 || target < 0 || target >= state.includedToolIds.length) return;
    const next = [...state.includedToolIds];
    [next[idx], next[target]] = [next[target], next[idx]];
    dispatch({ type: "SET_SELECTION", toolIds: next });
  }

  const publishedIds = state.includedToolIds.slice(0, state.finalCount);
  const missingLinks = publishedIds
    .map((id) => toolsById[id])
    .filter((t) => !t.website_url || !t.source_url);

  async function submit() {
    if (!state.selectedCategoryId) return;
    const result = await draftAction.run({
      category_id: state.selectedCategoryId,
      selected_tool_ids_in_order: state.includedToolIds,
      final_count: state.finalCount,
    });
    if (result) dispatch({ type: "DRAFT_SUCCESS", result });
  }

  return (
    <div className={styles.screen}>
      <h1>Human review</h1>
      <p>Which companies make the list, in what order, and how many - your call.</p>

      <div className={styles.table} role="table" aria-label="Candidate tools">
        {orderedIds.map((id) => {
          const tool = toolsById[id];
          const included = includedSet.has(id);
          const position = state.includedToolIds.indexOf(id);
          return (
            <div className={styles.row} key={id} role="row" data-excluded={!included}>
              <input
                type="checkbox"
                checked={included}
                onChange={() => toggleInclude(id)}
                aria-label={`Include ${tool.company_name}`}
              />
              <div className={styles.reorderBtns}>
                <button
                  type="button"
                  disabled={!included || position <= 0}
                  onClick={() => move(id, -1)}
                  aria-label={`Move ${tool.company_name} up`}
                >
                  ↑
                </button>
                <button
                  type="button"
                  disabled={!included || position >= state.includedToolIds.length - 1}
                  onClick={() => move(id, 1)}
                  aria-label={`Move ${tool.company_name} down`}
                >
                  ↓
                </button>
              </div>
              <span>{tool.company_name}</span>
              <span className={styles.meta}>{tool.aggregated_rating}★</span>
              <span className={styles.meta}>{tool.starting_price}</span>
              <StalenessBadge daysSinceUpdate={tool.days_since_update} />
            </div>
          );
        })}
      </div>

      <div className={styles.countRow}>
        <label htmlFor="final-count">Final count</label>
        <input
          id="final-count"
          type="number"
          min={1}
          max={Math.max(state.includedToolIds.length, 1)}
          value={state.finalCount}
          onChange={(e) =>
            dispatch({
              type: "SET_FINAL_COUNT",
              count: Math.min(Math.max(1, Number(e.target.value) || 1), state.includedToolIds.length),
            })
          }
        />
        <span className={styles.meta}>of {state.includedToolIds.length} included</span>
      </div>

      <div className={styles.readiness} data-ok={missingLinks.length === 0}>
        {missingLinks.length === 0
          ? `${publishedIds.length} companies selected, all have website URLs.`
          : `${missingLinks.length} of ${publishedIds.length} selected companies are missing a website or source URL - links will be broken in the draft.`}
      </div>

      {draftAction.error && <ErrorBanner message={draftAction.error} onRetry={submit} />}

      <button
        type="button"
        className={styles.submit}
        disabled={publishedIds.length === 0 || draftAction.loading}
        onClick={submit}
      >
        {draftAction.loading ? "Generating draft…" : "Generate draft"}
      </button>
    </div>
  );
}
