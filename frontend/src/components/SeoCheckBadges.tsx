import type { SeoChecksOut } from "../api/types";
import styles from "./SeoCheckBadges.module.css";

function Badge({ pass, children }: { pass: boolean; children: React.ReactNode }) {
  return (
    <span className={styles.badge} data-pass={pass}>
      {pass ? "✓" : "✗"} {children}
    </span>
  );
}

export function SeoCheckBadges({ checks }: { checks: SeoChecksOut }) {
  const p = checks.keyword_placements;
  return (
    <div className={styles.grid} role="list" aria-label="SEO readiness checks">
      <Badge pass={p.lexical_in_title}>Lexical keyword in title</Badge>
      <Badge pass={p.lexical_in_first_100_words}>Lexical keyword in first 100 words</Badge>
      <Badge pass={p.semantic_terms_missing.length === 0}>
        {p.semantic_terms_used.length}/{p.semantic_terms_used.length + p.semantic_terms_missing.length} semantic
        terms used
      </Badge>
      <Badge pass={p.intent_terms_in_faq > 0}>{p.intent_terms_in_faq} intent terms in FAQ</Badge>
      <Badge pass={checks.heading_structure_valid}>Heading structure valid</Badge>
      <Badge pass={checks.word_count >= 600}>{checks.word_count} words</Badge>
    </div>
  );
}
