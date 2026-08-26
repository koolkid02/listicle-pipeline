import type { Stage } from "../state/pipelineState";
import styles from "./PipelineRail.module.css";

const STAGES: { key: Stage; label: string; human: boolean }[] = [
  { key: "request", label: "1. Request", human: false },
  { key: "guardrail", label: "2. Guardrail & intent", human: false },
  { key: "retrieval", label: "3. Retrieval", human: false },
  { key: "review", label: "4. Human review", human: true },
  { key: "draft", label: "5. Draft", human: false },
];

export function PipelineRail({ currentStage }: { currentStage: Stage }) {
  return (
    <nav className={styles.rail} aria-label="Pipeline stages">
      {STAGES.map((s) => (
        <div key={s.key} className={styles.item} data-active={s.key === currentStage}>
          <span className={styles.dot} data-human={s.human} aria-hidden="true" />
          {s.label}
        </div>
      ))}
    </nav>
  );
}
