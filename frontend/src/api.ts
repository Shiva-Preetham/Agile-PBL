import type {
  ActionStatus,
  CustomerPage,
  CustomerProfile,
  DashboardSummary,
  Explanation,
  ModelMetrics,
  Prediction,
  Recommendation,
  RetentionAction,
  UploadResult,
} from "./types";

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
    response = await fetch(path, init);
  } catch {
    throw new ApiError(0, ["Cannot reach the ChurnSense API. Is the backend running on port 8000?"]);
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
  getRecommendation: (id: string) =>
    request<Recommendation>(`/api/customers/${encodeURIComponent(id)}/recommendation`),
  updateStatus: (id: string, status: ActionStatus) =>
    request<RetentionAction>(`/api/customers/${encodeURIComponent(id)}/action`, json("PATCH", { status })),
  dashboard: (filters: { contract_type?: string; internet_service?: string }) =>
    request<DashboardSummary>("/api/dashboard/summary" + query(filters)),
  metrics: () => request<ModelMetrics>("/api/model/metrics"),
  predict: (features: Record<string, string | number>) => request<Prediction>("/api/predict", json("POST", features)),
};
