import type {
  ClassifyRequest,
  ClassifyResponse,
  GenerateDraftRequest,
  GenerateDraftResponse,
  RetrievalResponse,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(0, "Could not reach the server. Check your connection and try again.");
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON; keep statusText
    }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<T>;
}

export function classify(req: ClassifyRequest): Promise<ClassifyResponse> {
  return request<ClassifyResponse>("/pipeline/classify", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function retrieval(categoryId: string): Promise<RetrievalResponse> {
  const params = new URLSearchParams({ category_id: categoryId });
  return request<RetrievalResponse>(`/pipeline/retrieval?${params}`);
}

export function generateDraft(req: GenerateDraftRequest): Promise<GenerateDraftResponse> {
  return request<GenerateDraftResponse>("/pipeline/generate-draft", {
    method: "POST",
    body: JSON.stringify(req),
  });
}
