import { useReducer } from "react";
import type { ClassifyResponse, GenerateDraftResponse, RetrievalResponse } from "../api/types";
import { buildFaqJsonLd } from "../lib/faqJsonLd";

export type Stage = "request" | "guardrail" | "retrieval" | "review" | "draft";

export interface PipelineState {
  stage: Stage;
  primaryKeyword: string;
  secondaryKeyword: string;
  classify: ClassifyResponse | null;
  selectedCategoryId: string | null;
  retrieval: RetrievalResponse | null;
  includedToolIds: string[];
  finalCount: number;
  draft: GenerateDraftResponse | null;
  draftEdited: boolean;
  sentForReview: boolean;
  sentAt: string | null;
}

export const initialPipelineState: PipelineState = {
  stage: "request",
  primaryKeyword: "",
  secondaryKeyword: "",
  classify: null,
  selectedCategoryId: null,
  retrieval: null,
  includedToolIds: [],
  finalCount: 5,
  draft: null,
  draftEdited: false,
  sentForReview: false,
  sentAt: null,
};

export type PipelineAction =
  | { type: "SET_REQUEST_FIELDS"; primaryKeyword: string; secondaryKeyword: string }
  | { type: "CLASSIFY_SUCCESS"; result: ClassifyResponse }
  | { type: "RETRIEVAL_SUCCESS"; result: RetrievalResponse }
  | { type: "SET_SELECTION"; toolIds: string[] }
  | { type: "SET_FINAL_COUNT"; count: number }
  | { type: "DRAFT_SUCCESS"; result: GenerateDraftResponse }
  | { type: "EDIT_TITLE"; value: string }
  | { type: "EDIT_SLUG"; value: string }
  | { type: "EDIT_META_DESCRIPTION"; value: string }
  | { type: "EDIT_LEDE"; html: string }
  | { type: "EDIT_SECTION"; toolId: string; field: "body_html" | "gaps_html"; html: string }
  | { type: "EDIT_FAQ"; index: number; field: "question" | "answer"; value: string }
  | { type: "SEND_FOR_REVIEW" }
  | { type: "SET_STAGE"; stage: Stage }
  | { type: "RESET" };

export function pipelineReducer(state: PipelineState, action: PipelineAction): PipelineState {
  switch (action.type) {
    case "SET_REQUEST_FIELDS":
      return { ...state, primaryKeyword: action.primaryKeyword, secondaryKeyword: action.secondaryKeyword };
    case "CLASSIFY_SUCCESS":
      return {
        ...state,
        classify: action.result,
        selectedCategoryId: action.result.category?.id ?? state.selectedCategoryId,
        stage: action.result.scope_ok ? "guardrail" : "request",
      };
    case "RETRIEVAL_SUCCESS": {
      const allIds = action.result.tools.map((t) => t.id);
      return {
        ...state,
        retrieval: action.result,
        includedToolIds: allIds,
        finalCount: Math.min(state.finalCount, allIds.length) || allIds.length,
      };
    }
    case "SET_SELECTION":
      return { ...state, includedToolIds: action.toolIds };
    case "SET_FINAL_COUNT":
      return { ...state, finalCount: action.count };
    case "DRAFT_SUCCESS":
      return {
        ...state,
        draft: action.result,
        stage: "draft",
        draftEdited: false,
        sentForReview: false,
        sentAt: null,
      };
    case "EDIT_TITLE":
      if (!state.draft) return state;
      return {
        ...state,
        draft: { ...state.draft, title: action.value },
        draftEdited: true,
        sentForReview: false,
        sentAt: null,
      };
    case "EDIT_SLUG":
      if (!state.draft) return state;
      return {
        ...state,
        draft: { ...state.draft, slug: action.value },
        draftEdited: true,
        sentForReview: false,
        sentAt: null,
      };
    case "EDIT_META_DESCRIPTION":
      if (!state.draft) return state;
      return {
        ...state,
        draft: { ...state.draft, meta_description: action.value },
        draftEdited: true,
        sentForReview: false,
        sentAt: null,
      };
    case "EDIT_LEDE":
      if (!state.draft) return state;
      return {
        ...state,
        draft: { ...state.draft, lede_html: action.html },
        draftEdited: true,
        sentForReview: false,
        sentAt: null,
      };
    case "EDIT_SECTION": {
      if (!state.draft) return state;
      const sections = state.draft.sections.map((s) =>
        s.tool_id === action.toolId ? { ...s, [action.field]: action.html } : s
      );
      return {
        ...state,
        draft: { ...state.draft, sections },
        draftEdited: true,
        sentForReview: false,
        sentAt: null,
      };
    }
    case "EDIT_FAQ": {
      if (!state.draft) return state;
      const faq = state.draft.faq.map((f, i) => (i === action.index ? { ...f, [action.field]: action.value } : f));
      return {
        ...state,
        draft: { ...state.draft, faq, faq_schema_jsonld: buildFaqJsonLd(faq) },
        draftEdited: true,
        sentForReview: false,
        sentAt: null,
      };
    }
    case "SEND_FOR_REVIEW":
      return { ...state, sentForReview: true, sentAt: new Date().toISOString() };
    case "SET_STAGE":
      return { ...state, stage: action.stage };
    case "RESET":
      return initialPipelineState;
    default:
      return state;
  }
}

export function usePipelineState() {
  return useReducer(pipelineReducer, initialPipelineState);
}
