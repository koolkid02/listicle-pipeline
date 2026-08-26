import { useCallback, useState } from "react";
import { ApiError } from "../api/client";

interface AsyncActionState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useAsyncAction<TArgs extends unknown[], TResult>(
  fn: (...args: TArgs) => Promise<TResult>
) {
  const [state, setState] = useState<AsyncActionState<TResult>>({
    data: null,
    loading: false,
    error: null,
  });

  const run = useCallback(
    async (...args: TArgs) => {
      setState({ data: null, loading: true, error: null });
      try {
        const result = await fn(...args);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
        setState({ data: null, loading: false, error: message });
        return null;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const reset = useCallback(() => setState({ data: null, loading: false, error: null }), []);

  return { ...state, run, reset };
}
