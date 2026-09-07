import { useState, useCallback } from "react";
import { analyzeCode, getHint } from "../services/api";
import type { AnalyzeRequestBody, AnalyzeResponse, ApiErrorShape } from "../types";

interface UseAnalyzeState {
  loading: boolean;
  hintLoading: boolean;
  error: string | null;
  result: AnalyzeResponse | null;
  hint: string | null;
}

export function useAnalyze() {
  const [state, setState] = useState<UseAnalyzeState>({
    loading: false,
    hintLoading: false,
    error: null,
    result: null,
    hint: null,
  });

  const runAnalysis = useCallback(async (body: AnalyzeRequestBody) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await analyzeCode(body);
      setState((prev) => ({ ...prev, loading: false, result }));
    } catch (err) {
      const apiError = err as ApiErrorShape;
      setState((prev) => ({ ...prev, loading: false, error: apiError.message }));
    }
  }, []);

  const requestHint = useCallback(async (body: Omit<AnalyzeRequestBody, "question">) => {
    setState((prev) => ({ ...prev, hintLoading: true, error: null }));
    try {
      const hint = await getHint(body);
      setState((prev) => ({ ...prev, hintLoading: false, hint }));
    } catch (err) {
      const apiError = err as ApiErrorShape;
      setState((prev) => ({ ...prev, hintLoading: false, error: apiError.message }));
    }
  }, []);

  const reset = useCallback(() => {
    setState({ loading: false, hintLoading: false, error: null, result: null, hint: null });
  }, []);

  return { ...state, runAnalysis, requestHint, reset };
}
