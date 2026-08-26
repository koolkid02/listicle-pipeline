import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { sanitizeHtml } from "../lib/sanitize";
import styles from "./EditableHtml.module.css";

export function EditableHtml({
  html,
  onSave,
  ariaLabel,
}: {
  html: string;
  onSave: (html: string) => void;
  ariaLabel: string;
}) {
  const [editing, setEditing] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // React clears innerHTML when dangerouslySetInnerHTML is omitted on a re-render
    // (entering edit mode), so the editable content has to be seeded manually here
    // rather than relying on the DOM being left alone.
    if (editing && ref.current) {
      ref.current.innerHTML = sanitizeHtml(html);
      ref.current.focus();
    }
    // Only re-seed when edit mode is entered, not on every `html` change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editing]);

  function save() {
    const raw = ref.current?.innerHTML ?? "";
    // contentEditable output can carry browser-injected formatting - re-sanitize
    // before it ever gets committed to state.
    onSave(sanitizeHtml(raw));
    setEditing(false);
  }

  function cancel() {
    setEditing(false);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      cancel();
    }
  }

  return (
    <div className={styles.container}>
      {!editing && (
        <button type="button" className={styles.editBtn} onClick={() => setEditing(true)}>
          Edit {ariaLabel}
        </button>
      )}
      <div
        ref={ref}
        className={styles.content}
        contentEditable={editing}
        suppressContentEditableWarning
        role={editing ? "textbox" : undefined}
        aria-multiline={editing ? true : undefined}
        aria-label={editing ? ariaLabel : undefined}
        onKeyDown={handleKeyDown}
        {...(!editing ? { dangerouslySetInnerHTML: { __html: sanitizeHtml(html) } } : {})}
      />
      {editing && (
        <div className={styles.editActions}>
          <button type="button" onClick={save}>
            Save
          </button>
          <button type="button" onClick={cancel}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
