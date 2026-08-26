import DOMPurify from "dompurify";

// The only path to dangerouslySetInnerHTML in this app. body_html/gaps_html/lede_html
// come from a formatter stage backed by an LLM - never render them raw.
export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, { ALLOWED_TAGS: ["p", "ul", "ol", "li", "strong", "em", "br"] });
}
