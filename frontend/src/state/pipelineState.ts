import { useReducer } from "react";
import type { ClassifyResponse, GenerateDraftResponse, RetrievalResponse } from "../api/types";

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
};

export type PipelineAction =
  | { type: "SET_REQUEST_FIELDS"; primaryKeyword: string; secondaryKeyword: string }
  | { type: "CLASSIFY_SUCCESS"; result: ClassifyResponse }
  | { type: "RETRIEVAL_SUCCESS"; result: RetrievalResponse }
  | { type: "SET_SELECTION"; toolIds: string[] }
  | { type: "SET_FINAL_COUNT"; count: number }
  | { type: "DRAFT_SUCCESS"; result: GenerateDraftResponse }
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
      return { ...state, draft: action.result, stage: "draft" };
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
