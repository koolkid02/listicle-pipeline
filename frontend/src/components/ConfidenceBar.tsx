import styles from "./ConfidenceBar.module.css";

export function ConfidenceBar({ confidence, blocked }: { confidence: number; blocked: boolean }) {
  return (
    <div>
      <div className={styles.label}>
        <span>Category confidence</span>
        <span>{confidence}%</span>
      </div>
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={confidence}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Category classification confidence"
      >
        <div className={styles.fill} data-blocked={blocked} style={{ width: `${confidence}%` }} />
      </div>
    </div>
  );
}
