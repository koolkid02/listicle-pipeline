export interface CategoryOut {
  id: string;
  name: string;
}

export interface ClassifyRequest {
  primary_keyword: string;
  secondary_keyword: string | null;
  manual_category_id: string | null;
}

export interface ClassifyResponse {
  scope_ok: boolean;
  category: CategoryOut | null;
  confidence: number;
  blocked: boolean;
  available_categories: CategoryOut[];
  reason: string | null;
}

export interface ToolOut {
  id: string;
  company_name: string;
  positioning: string;
  starting_price: string;
  aggregated_rating: number;
  review_count: number;
  what_it_does_well: string[];
  gaps: string[];
  best_for: string;
  website_url: string;
  source_url: string;
  last_updated: string;
  days_since_update: number;
}

export interface SemanticKeywordOut {
  term: string;
  similarity_score: number;
}

export interface IntentKeywordOut {
  term: string;
  stage: "informational" | "commercial_investigation" | "comparison";
}

export interface KeywordSetOut {
  lexical: string[];
  semantic: SemanticKeywordOut[];
  intent: IntentKeywordOut[];
}

export interface RetrievalResponse {
  tools: ToolOut[];
  keywords: KeywordSetOut;
}

export interface GenerateDraftRequest {
  category_id: string;
  selected_tool_ids_in_order: string[];
  final_count: number;
}

export interface SectionOut {
  rank: number;
  tool_id: string;
  company_name: string;
  website_url: string;
  source_url: string;
  body_html: string;
  gaps_html: string;
}

export interface FaqOut {
  question: string;
  answer: string;
}

export interface KeywordPlacementsOut {
  lexical_in_title: boolean;
  lexical_in_first_100_words: boolean;
  semantic_terms_used: string[];
  semantic_terms_missing: string[];
  intent_terms_in_faq: number;
}

export interface SeoChecksOut {
  word_count: number;
  heading_structure_valid: boolean;
  keyword_placements: KeywordPlacementsOut;
}

export interface GenerateDraftResponse {
  title: string;
  slug: string;
  meta_description: string;
  lede_html: string;
  sections: SectionOut[];
  faq: FaqOut[];
  faq_schema_jsonld: Record<string, unknown>;
  seo_checks: SeoChecksOut;
}
