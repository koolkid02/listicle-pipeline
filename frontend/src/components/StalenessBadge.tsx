import styles from "./StalenessBadge.module.css";

export const STALENESS_THRESHOLD_DAYS = 60;

export function StalenessBadge({ daysSinceUpdate }: { daysSinceUpdate: number }) {
  if (daysSinceUpdate <= STALENESS_THRESHOLD_DAYS) return null;
  return (
    <span className={styles.badge}>
      ⚠ stale · {daysSinceUpdate}d
    </span>
  );
}
