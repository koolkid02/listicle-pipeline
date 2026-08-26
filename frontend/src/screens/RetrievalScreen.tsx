import { useEffect, type Dispatch } from "react";
import { retrieval } from "../api/client";
import { StalenessBadge } from "../components/StalenessBadge";
import { ErrorBanner } from "../components/ErrorBanner";
import { useAsyncAction } from "../lib/useAsyncAction";
import type { PipelineAction, PipelineState } from "../state/pipelineState";
import styles from "./RetrievalScreen.module.css";

export function RetrievalScreen({
  state,
  dispatch,
}: {
  state: PipelineState;
  dispatch: Dispatch<PipelineAction>;
}) {
  const retrievalAction = useAsyncAction(retrieval);
  const categoryId = state.selectedCategoryId;

  useEffect(() => {
    if (!categoryId || state.retrieval) return;
    (async () => {
      const result = await retrievalAction.run(categoryId);
      if (result) dispatch({ type: "RETRIEVAL_SUCCESS", result });
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryId]);

  if (retrievalAction.loading) return <p>Loading retrieval data…</p>;
  if (retrievalAction.error) {
    return (
      <ErrorBanner
        message={retrievalAction.error}
        onRetry={() => categoryId && retrievalAction.run(categoryId).then((r) => r && dispatch({ type: "RETRIEVAL_SUCCESS", result: r }))}
      />
    );
  }

  const data = state.retrieval;
  if (!data) return null;

  return (
    <div className={styles.screen}>
      <h1>Retrieval</h1>
      <p>Read-only - sanity-check what retrieval found before moving to review.</p>

      <div className={styles.columns}>
        <div>
          {data.tools.map((tool) => (
            <div key={tool.id} className={styles.toolCard}>
              <div>
                <strong>{tool.company_name}</strong>
                <p>{tool.positioning}</p>
              </div>
              <div className={styles.toolMeta}>
                <span>{tool.aggregated_rating}★</span>
                <span>{tool.starting_price}</span>
                <StalenessBadge daysSinceUpdate={tool.days_since_update} />
              </div>
            </div>
          ))}
        </div>

        <div>
          <div className={styles.keywordGroup}>
            <h3>Lexical</h3>
            <div className={styles.keywordChips}>
              {data.keywords.lexical.map((kw) => (
                <span key={kw} className={styles.kwLexical}>
                  {kw}
                </span>
              ))}
            </div>
          </div>
          <div className={styles.keywordGroup}>
            <h3>Semantic</h3>
            <div className={styles.keywordChips}>
              {data.keywords.semantic.map((kw) => (
                <span key={kw.term} className={styles.kwSemantic}>
                  {kw.term} · {kw.similarity_score.toFixed(2)}
                </span>
              ))}
            </div>
          </div>
          <div className={styles.keywordGroup}>
            <h3>Intent</h3>
            <div className={styles.keywordChips}>
              {data.keywords.intent.map((kw) => (
                <span key={kw.term} className={styles.kwIntent}>
                  {kw.term} · {kw.stage}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <button type="button" className={styles.continue} onClick={() => dispatch({ type: "SET_STAGE", stage: "review" })}>
        Continue to review
      </button>
    </div>
  );
}
