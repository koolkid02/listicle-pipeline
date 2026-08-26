import { useState, type Dispatch } from "react";
import { classify } from "../api/client";
import { STATIC_CATEGORIES } from "../api/staticCategories";
import { ErrorBanner } from "../components/ErrorBanner";
import { useAsyncAction } from "../lib/useAsyncAction";
import type { PipelineAction, PipelineState } from "../state/pipelineState";
import styles from "./RequestScreen.module.css";

export function RequestScreen({
  state,
  dispatch,
}: {
  state: PipelineState;
  dispatch: Dispatch<PipelineAction>;
}) {
  const [primaryKeyword, setPrimaryKeyword] = useState(state.primaryKeyword);
  const [secondaryKeyword, setSecondaryKeyword] = useState(state.secondaryKeyword);
  const [selectedChipId, setSelectedChipId] = useState<string | null>(null);
  const classifyAction = useAsyncAction(classify);

  const canSubmit = primaryKeyword.trim().length > 0 || selectedChipId !== null;

  async function submit() {
    dispatch({ type: "SET_REQUEST_FIELDS", primaryKeyword, secondaryKeyword });
    const result = await classifyAction.run({
      primary_keyword: primaryKeyword.trim(),
      secondary_keyword: secondaryKeyword.trim() || null,
      manual_category_id: selectedChipId,
    });
    if (result) {
      dispatch({ type: "CLASSIFY_SUCCESS", result });
    }
  }

  const scopeError = classifyAction.data && !classifyAction.data.scope_ok ? classifyAction.data.reason : null;

  return (
    <div className={styles.screen}>
      <h1>What listicle do you need?</h1>

      <div className={styles.field}>
        <label htmlFor="primary-keyword">Primary keyword</label>
        <input
          id="primary-keyword"
          value={primaryKeyword}
          onChange={(e) => setPrimaryKeyword(e.target.value)}
          placeholder="e.g. event registration software"
        />
      </div>

      <div className={styles.field}>
        <label htmlFor="secondary-keyword">Secondary keyword (optional)</label>
        <input
          id="secondary-keyword"
          value={secondaryKeyword}
          onChange={(e) => setSecondaryKeyword(e.target.value)}
          placeholder="e.g. ticketing platform"
        />
      </div>

      <div className={styles.field}>
        <span id="category-chips-label">Or pick a category directly (skips classification)</span>
        <div className={styles.chips} role="group" aria-labelledby="category-chips-label">
          {STATIC_CATEGORIES.map((c) => (
            <button
              key={c.id}
              type="button"
              className={styles.chip}
              data-selected={selectedChipId === c.id}
              aria-pressed={selectedChipId === c.id}
              onClick={() => setSelectedChipId((prev) => (prev === c.id ? null : c.id))}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {(scopeError || classifyAction.error) && (
        <ErrorBanner message={scopeError ?? classifyAction.error ?? ""} onRetry={submit} />
      )}

      <button type="button" className={styles.submit} disabled={!canSubmit || classifyAction.loading} onClick={submit}>
        {classifyAction.loading ? "Checking…" : "Continue"}
      </button>
    </div>
  );
}
