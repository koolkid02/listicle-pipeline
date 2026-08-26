import type { FaqOut } from "../api/types";

// Mirrors api/faq_jsonld.py's build_faq_jsonld exactly, so an edited FAQ item's
// JSON-LD stays correct without a round-trip to the backend.
export function buildFaqJsonLd(faq: FaqOut[]): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: item.answer },
    })),
  };
}
