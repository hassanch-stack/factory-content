// Cliente mínimo del API. En Phase 1 esto se sustituirá por un cliente
// tipado generado desde el OpenAPI schema de FastAPI (punto 20 del spec).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function operatorHeaders(headers: HeadersInit = {}): HeadersInit {
  if (typeof window === "undefined") return headers;
  const token = window.localStorage.getItem("factor_operator_token");
  return token ? { ...headers, Authorization: `Bearer ${token}` } : headers;
}

export type Source = {
  id: string;
  name: string;
  platform: string;
  permission_status: string;
  active: boolean;
};

export type ContentItem = {
  id: string;
  title: string | null;
  status: string;
  factor_score: number;
  rights_status: string;
};

export type MediaAsset = {
  id: string;
  content_item_id: string;
  asset_type: string;
  mime_type: string | null;
  width: number | null;
  height: number | null;
  file_size: number | null;
  created_at: string;
};

export type VisualTemplate = {
  id: string;
  name: string;
  version: number;
  configuration_json: Record<string, unknown>;
};

export type ScriptTemplate = VisualTemplate;

export type AIGeneration = {
  id: string;
  output_json: Record<string, unknown>;
  edited_by_user: boolean;
};

export type Account = {
  id: string;
  name: string;
  platform: string;
  username: string | null;
  timezone: string;
  active: boolean;
  publishing_enabled: boolean;
};

export type Post = {
  id: string;
  content_item_id: string;
  account_id: string;
  platform: string;
  scheduled_at: string;
  status: string;
};

export type DashboardKpis = {
  total_views: number;
  views_per_post: number;
  median_views: number;
  engagement_rate: number;
  avg_completion_rate: number;
  followers_gained: number;
};

export type ReviewItem = {
  content_item_id: string;
  title: string | null;
  status: string;
  rights_status: string;
  factor_score: number;
  ai_output: {
    hook?: string;
    sections?: Record<string, string>;
    cta?: string;
    title?: string;
    hashtags?: string[];
    keywords?: string[];
  } | null;
  preview: { media_asset_id: string; preview_url: string; asset_type: string } | null;
};

export async function getHealth() {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  return res.json();
}

export async function getSources(): Promise<Source[]> {
  const res = await fetch(`${API_URL}/api/sources`, { cache: "no-store", headers: operatorHeaders() });
  if (!res.ok) return [];
  return res.json();
}

export async function getContentQueue(status?: string): Promise<ContentItem[]> {
  const url = status
    ? `${API_URL}/api/content?status=${status}`
    : `${API_URL}/api/content`;
  const res = await fetch(url, { cache: "no-store", headers: operatorHeaders() });
  if (!res.ok) return [];
  return res.json();
}

export type ManualImportResult = ContentItem & {
  media_asset_id: string;
  mime_type: string;
  width: number;
  height: number;
  file_size: number;
};

export async function importManualContent(formData: FormData): Promise<ManualImportResult> {
  const res = await fetch(`${API_URL}/api/content/import`, {
    method: "POST",
    body: formData,
    headers: operatorHeaders(),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;
    const message = typeof detail === "string" ? detail : detail?.message;
    throw new Error(message ?? "No se pudo importar la foto.");
  }
  return res.json();
}

async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: operatorHeaders({ "Content-Type": "application/json", ...(init?.headers ?? {}) }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : "La operación no se pudo completar.");
  }
  return res.json();
}

export function getContentAssets(contentId: string): Promise<MediaAsset[]> {
  return apiJson(`/api/content/${contentId}/assets`);
}

export function getVisualTemplates(): Promise<VisualTemplate[]> {
  return apiJson("/api/templates");
}

export function getScriptTemplates(): Promise<ScriptTemplate[]> {
  return apiJson("/api/script-templates");
}

export function rewriteScript(contentItemId: string, scriptTemplateId: string): Promise<AIGeneration> {
  return apiJson("/api/ai/rewrite-script", {
    method: "POST",
    body: JSON.stringify({ content_item_id: contentItemId, script_template_id: scriptTemplateId }),
  });
}

export function updateGeneration(generationId: string, outputJson: Record<string, unknown>): Promise<AIGeneration> {
  return apiJson(`/api/ai/generations/${generationId}`, {
    method: "PATCH",
    body: JSON.stringify({ output_json: outputJson }),
  });
}

export function enqueueRenders(payload: {
  content_item_id: string;
  template_id: string;
  input_asset_id: string;
  slide_index: number;
}[]) {
  return apiJson("/api/render/bulk", { method: "POST", body: JSON.stringify(payload) });
}

export function getAccounts(): Promise<Account[]> {
  return apiJson("/api/accounts");
}

export function createAccount(payload: Omit<Account, "id" | "active">): Promise<Account> {
  return apiJson("/api/accounts", { method: "POST", body: JSON.stringify(payload) });
}

export function getPosts(): Promise<Post[]> {
  return apiJson("/api/posts");
}

export function createSchedule(payload: {
  content_item_id: string;
  account_id: string;
  platform: string;
  scheduled_at: string;
}): Promise<Post> {
  return apiJson("/api/schedules", { method: "POST", body: JSON.stringify(payload) });
}

export function getAnalyticsOverview(): Promise<DashboardKpis> {
  return apiJson("/api/analytics/overview");
}

export function createVisualTemplate(name: string, configurationJson: Record<string, unknown>): Promise<VisualTemplate> {
  return apiJson("/api/templates", { method: "POST", body: JSON.stringify({ name, configuration_json: configurationJson }) });
}

export function createScriptTemplate(name: string, configurationJson: Record<string, unknown>): Promise<ScriptTemplate> {
  return apiJson("/api/script-templates", { method: "POST", body: JSON.stringify({ name, configuration_json: configurationJson }) });
}

export async function getReviewQueue(): Promise<ReviewItem[]> {
  const res = await fetch(`${API_URL}/api/review`, { cache: "no-store", headers: operatorHeaders() });
  if (!res.ok) return [];
  return res.json();
}

export async function approveReviewItem(id: string) {
  return fetch(`${API_URL}/api/review/${id}/approve`, { method: "POST", headers: operatorHeaders() });
}

export async function rejectReviewItem(id: string, reason?: string) {
  return fetch(`${API_URL}/api/review/${id}/reject`, {
    method: "POST",
    headers: operatorHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ reason }),
  });
}

export async function sendBackReviewItem(id: string) {
  return fetch(`${API_URL}/api/review/${id}/send-back`, { method: "POST", headers: operatorHeaders() });
}
