import { useMemo, useState, type Dispatch } from "react";
import { generateDraft } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { SeoCheckBadges } from "../components/SeoCheckBadges";
import { useAsyncAction } from "../lib/useAsyncAction";
import { sanitizeHtml } from "../lib/sanitize";
import type { PipelineAction, PipelineState } from "../state/pipelineState";
import styles from "./DraftScreen.module.css";

function safeJsonLd(data: unknown): string {
  // Prevent a `</script>` inside a string value from breaking out of the script tag.
  return JSON.stringify(data).replace(/</g, "\\u003c");
}

export function DraftScreen({
  state,
  dispatch,
}: {
  state: PipelineState;
  dispatch: Dispatch<PipelineAction>;
}) {
  const draft = state.draft;
  const regenerateAction = useAsyncAction(generateDraft);
  const [copied, setCopied] = useState<"text" | "html" | null>(null);

  const toolsById = useMemo(
    () => Object.fromEntries((state.retrieval?.tools ?? []).map((t) => [t.id, t])),
    [state.retrieval]
  );

  if (!draft) return null;

  async function regenerate() {
    if (!state.selectedCategoryId) return;
    const result = await regenerateAction.run({
      category_id: state.selectedCategoryId,
      selected_tool_ids_in_order: state.includedToolIds,
      final_count: state.finalCount,
    });
    if (result) dispatch({ type: "DRAFT_SUCCESS", result });
  }

  function articleHtml(): string {
    const parts = [
      `<h1>${draft!.title}</h1>`,
      `<p>${draft!.meta_description}</p>`,
      sanitizeHtml(draft!.lede_html),
    ];
    for (const s of draft!.sections) {
      parts.push(`<h2>${s.company_name}</h2>`, sanitizeHtml(s.body_html), sanitizeHtml(s.gaps_html));
    }
    parts.push("<h2>FAQ</h2>");
    for (const f of draft!.faq) {
      parts.push(`<h3>${f.question}</h3><p>${f.answer}</p>`);
    }
    return parts.join("\n");
  }

  async function copyAsHtml() {
    await navigator.clipboard.writeText(articleHtml());
    setCopied("html");
  }

  async function copyAsText() {
    const doc = new DOMParser().parseFromString(articleHtml(), "text/html");
    await navigator.clipboard.writeText(doc.body.textContent?.trim() ?? "");
    setCopied("text");
  }

  return (
    <div className={styles.screen}>
      <SeoCheckBadges checks={draft.seo_checks} />

      <div className={styles.actions}>
        <button type="button" onClick={regenerate} disabled={regenerateAction.loading}>
          {regenerateAction.loading ? "Regenerating…" : "Regenerate"}
        </button>
        <button type="button" onClick={copyAsText}>
          {copied === "text" ? "Copied!" : "Copy as text"}
        </button>
        <button type="button" onClick={copyAsHtml}>
          {copied === "html" ? "Copied!" : "Copy as HTML"}
        </button>
      </div>

      {regenerateAction.error && <ErrorBanner message={regenerateAction.error} onRetry={regenerate} />}

      <article className={styles.article}>
        <h1>{draft.title}</h1>
        <p className={styles.metaDescription}>{draft.meta_description}</p>

        <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(draft.lede_html) }} />

        <table className={styles.table}>
          <thead>
            <tr>
              <th>Tool</th>
              <th>Best for</th>
              <th>Starting price</th>
              <th>G2 rating</th>
            </tr>
          </thead>
          <tbody>
            {draft.sections.map((s) => {
              const tool = toolsById[s.tool_id];
              return (
                <tr key={s.tool_id}>
                  <td>{s.company_name}</td>
                  <td>{tool?.best_for ?? "—"}</td>
                  <td>{tool?.starting_price ?? "—"}</td>
                  <td>{tool ? `${tool.aggregated_rating}★` : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {draft.sections.map((s) => (
          <section className={styles.section} key={s.tool_id}>
            <h2>{s.company_name}</h2>
            <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(s.body_html) }} />
            {s.gaps_html && (
              <>
                <p className={styles.gapsHeading}>Where it falls short</p>
                <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(s.gaps_html) }} />
              </>
            )}
            <p>
              <a href={s.website_url} target="_blank" rel="noreferrer">
                Visit {s.company_name} →
              </a>
            </p>
          </section>
        ))}

        <section className={styles.section}>
          <h2>FAQ</h2>
          {draft.faq.map((f) => (
            <div className={styles.faqItem} key={f.question}>
              <h3>{f.question}</h3>
              <p>{f.answer}</p>
            </div>
          ))}
        </section>
      </article>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: safeJsonLd(draft.faq_schema_jsonld) }} />
    </div>
  );
}
