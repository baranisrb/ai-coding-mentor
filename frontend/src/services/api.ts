import axios, { AxiosError } from "axios";
import type { AnalyzeRequestBody, AnalyzeResponse, ApiErrorShape } from "../types";

// The Gemini API key never lives in the frontend. This is just the base
// URL of our own backend, which is the only thing allowed to talk to
// Gemini.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const client = axios.create({
  baseURL: API_URL,
  timeout: 60_000,
});

function toApiError(error: unknown): ApiErrorShape {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
    const status = axiosError.response?.status ?? 0;
    const detail = axiosError.response?.data?.detail || axiosError.response?.data?.error;
    if (status === 0) {
      return { status, message: "Could not reach the backend. Is it running?" };
    }
    if (status === 429) {
      return { status, message: detail || "Free AI API limit reached. Please wait and try again." };
    }
    if (status === 413) {
      return { status, message: detail || "Your code is too large." };
    }
    if (status === 503) {
      return { status, message: detail || "The AI mentor is not configured on the server." };
    }
    return { status, message: detail || "Something went wrong while analyzing your code." };
  }
  return { status: 0, message: "An unexpected error occurred." };
}

export async function analyzeCode(body: AnalyzeRequestBody): Promise<AnalyzeResponse> {
  try {
    const response = await client.post<AnalyzeResponse>("/analyze", body);
    return response.data;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function getHint(body: Omit<AnalyzeRequestBody, "question">): Promise<string> {
  try {
    const response = await client.post<{ hint: string }>("/hint", body);
    return response.data.hint;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await client.get("/health");
    return response.data?.status === "ok";
  } catch {
    return false;
  }
}
