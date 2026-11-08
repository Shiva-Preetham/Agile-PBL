import type {
  ActionStatus,
  CustomerPage,
  CustomerProfile,
  DashboardSummary,
  Explanation,
  ModelMetrics,
  NextBestAction,
  Prediction,
  RetentionAction,
  UploadResult,
} from "./types";

/** Hosted build: the Render backend address. Local dev: empty, so Vite's proxy forwards /api. */
export const API_BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");

/** An API error with human-readable messages taken from the backend response. */
export class ApiError extends Error {
  constructor(public status: number, public messages: string[]) {
    super(messages.join("\n"));
  }
}

function extractMessages(body: unknown, fallback: string): string[] {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return [detail];
  if (detail && typeof detail === "object" && "errors" in detail) {
    return (detail as { errors: string[] }).errors;
  }
  if (Array.isArray(detail)) return detail.map((d) => String(d?.msg ?? d));
  return [fallback];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(API_BASE + path, init);
  } catch {
    const where = API_BASE ? `at ${API_BASE}` : "on port 8000 (is the backend running?)";
    throw new ApiError(0, [`Cannot reach the ChurnSense API ${where}.`]);
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, extractMessages(body, `Request failed (${response.status}).`));
  }
  return body as T;
}

function query(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== "");
  return entries.length ? "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])) : "";
}

const json = (method: string, data: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

export const api = {
  health: () => request<{ status: string; version: string }>("/api/health"),
  uploadCsv(file: File) {
    const form = new FormData();
    form.append("file", file);
    return request<UploadResult>("/api/customers/upload", { method: "POST", body: form });
  },
  listCustomers(params: { search?: string; risk?: string; contract_type?: string; page?: number; page_size?: number }) {
    return request<CustomerPage>("/api/customers" + query(params));
  },
  getCustomer: (id: string) => request<CustomerProfile>(`/api/customers/${encodeURIComponent(id)}`),
  getExplanation: (id: string) => request<Explanation>(`/api/customers/${encodeURIComponent(id)}/explanation`),
  getNextBestAction: (id: string) =>
    request<NextBestAction>(`/api/customers/${encodeURIComponent(id)}/next-best-action`),
  updateStatus: (id: string, status: ActionStatus) =>
    request<RetentionAction>(`/api/customers/${encodeURIComponent(id)}/action`, json("PATCH", { status })),
  dashboard: (filters: { contract_type?: string; internet_service?: string }) =>
    request<DashboardSummary>("/api/dashboard/summary" + query(filters)),
  metrics: () => request<ModelMetrics>("/api/model/metrics"),
  predict: (features: Record<string, string | number>) => request<Prediction>("/api/predict", json("POST", features)),
};
