import { useRef, useState, type KeyboardEvent } from "react";
import styles from "./EditableText.module.css";

export function EditableText({
  value,
  onSave,
  ariaLabel,
  multiline = false,
}: {
  value: string;
  onSave: (value: string) => void;
  ariaLabel: string;
  multiline?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function save() {
    const el = multiline ? textareaRef.current : inputRef.current;
    if (el) onSave(el.value);
    setEditing(false);
  }

  function cancel() {
    setEditing(false);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      cancel();
    } else if (e.key === "Enter" && !multiline && !e.shiftKey) {
      e.preventDefault();
      save();
    }
  }

  if (!editing) {
    return (
      <span className={styles.wrapper}>
        <span>{value}</span>
        <button type="button" className={styles.editBtn} onClick={() => setEditing(true)}>
          Edit {ariaLabel}
        </button>
      </span>
    );
  }

  return (
    <span className={styles.wrapper}>
      {multiline ? (
        <textarea
          ref={textareaRef}
          defaultValue={value}
          className={styles.textarea}
          aria-label={ariaLabel}
          onKeyDown={handleKeyDown}
          autoFocus
        />
      ) : (
        <input
          ref={inputRef}
          defaultValue={value}
          className={styles.input}
          aria-label={ariaLabel}
          onKeyDown={handleKeyDown}
          autoFocus
        />
      )}
      <span className={styles.editActions}>
        <button type="button" onClick={save}>
          Save
        </button>
        <button type="button" onClick={cancel}>
          Cancel
        </button>
      </span>
    </span>
  );
}
