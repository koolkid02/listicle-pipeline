import type { Dispatch } from "react";
import { classify } from "../api/client";
import { ConfidenceBar } from "../components/ConfidenceBar";
import { ErrorBanner } from "../components/ErrorBanner";
import { useAsyncAction } from "../lib/useAsyncAction";
import type { PipelineAction, PipelineState } from "../state/pipelineState";
import styles from "./GuardrailScreen.module.css";

export function GuardrailScreen({
  state,
  dispatch,
}: {
  state: PipelineState;
  dispatch: Dispatch<PipelineAction>;
}) {
  const pickAction = useAsyncAction(classify);
  const result = state.classify;
  if (!result) return null;

  async function pickCategory(categoryId: string) {
    const updated = await pickAction.run({
      primary_keyword: state.primaryKeyword,
      secondary_keyword: state.secondaryKeyword || null,
      manual_category_id: categoryId,
    });
    if (updated) dispatch({ type: "CLASSIFY_SUCCESS", result: updated });
  }

  return (
    <div className={styles.screen}>
      <h1>Guardrail &amp; intent</h1>

      <div className={styles.checkRow}>
        <span className={styles.pass} aria-hidden="true">
          ✓
        </span>
        Scope guardrail passed
      </div>

      <ConfidenceBar confidence={result.confidence} blocked={result.blocked} />

      {pickAction.error && <ErrorBanner message={pickAction.error} />}

      {result.blocked ? (
        <div>
          <p>Confidence is below threshold - pick the category directly:</p>
          <div className={styles.chips} role="group" aria-label="Available categories">
            {result.available_categories.map((c) => (
              <button
                key={c.id}
                type="button"
                className={styles.chip}
                disabled={pickAction.loading}
                onClick={() => pickCategory(c.id)}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div>
          <p>
            Matched category: <strong>{result.category?.name}</strong>
          </p>
          <button
            type="button"
            className={styles.continue}
            onClick={() => dispatch({ type: "SET_STAGE", stage: "retrieval" })}
          >
            Continue to retrieval
          </button>
        </div>
      )}
    </div>
  );
}
