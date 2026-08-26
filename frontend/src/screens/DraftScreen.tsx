import { useMemo, useState, type Dispatch } from "react";
import { generateDraft } from "../api/client";
import { EditableHtml } from "../components/EditableHtml";
import { EditableText } from "../components/EditableText";
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
    if (state.draftEdited && !window.confirm("Regenerating will discard your edits. Continue?")) {
      return;
    }
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
        <button
          type="button"
          className={styles.sendButton}
          onClick={() => dispatch({ type: "SEND_FOR_REVIEW" })}
          disabled={state.sentForReview}
        >
          {state.sentForReview ? "Sent for review ✓" : "Send for review"}
        </button>
        {state.sentForReview && state.sentAt && (
          <span className={styles.sentCaption}>
            Sent {new Date(state.sentAt).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
          </span>
        )}
      </div>

      {regenerateAction.error && <ErrorBanner message={regenerateAction.error} onRetry={regenerate} />}

      <article className={styles.article}>
        <h1>
          <EditableText value={draft.title} ariaLabel="title" onSave={(value) => dispatch({ type: "EDIT_TITLE", value })} />
        </h1>
        <p className={styles.metaDescription}>
          <EditableText
            value={draft.meta_description}
            ariaLabel="meta description"
            multiline
            onSave={(value) => dispatch({ type: "EDIT_META_DESCRIPTION", value })}
          />
        </p>

        <EditableHtml html={draft.lede_html} ariaLabel="intro" onSave={(html) => dispatch({ type: "EDIT_LEDE", html })} />

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
            <EditableHtml
              html={s.body_html}
              ariaLabel={`${s.company_name} summary`}
              onSave={(html) => dispatch({ type: "EDIT_SECTION", toolId: s.tool_id, field: "body_html", html })}
            />
            {s.gaps_html && (
              <>
                <p className={styles.gapsHeading}>Where it falls short</p>
                <EditableHtml
                  html={s.gaps_html}
                  ariaLabel={`${s.company_name} gaps`}
                  onSave={(html) => dispatch({ type: "EDIT_SECTION", toolId: s.tool_id, field: "gaps_html", html })}
                />
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
          {draft.faq.map((f, index) => (
            <div className={styles.faqItem} key={index}>
              <h3>
                <EditableText
                  value={f.question}
                  ariaLabel={`FAQ question ${index + 1}`}
                  onSave={(value) => dispatch({ type: "EDIT_FAQ", index, field: "question", value })}
                />
              </h3>
              <p>
                <EditableText
                  value={f.answer}
                  ariaLabel={`FAQ answer ${index + 1}`}
                  multiline
                  onSave={(value) => dispatch({ type: "EDIT_FAQ", index, field: "answer", value })}
                />
              </p>
            </div>
          ))}
        </section>
      </article>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: safeJsonLd(draft.faq_schema_jsonld) }} />
    </div>
  );
}
