/* The one place that talks to the backend. Errors surface the API's own
   `detail` message, which is written for the user ("upload a resume first"),
   not a bare status code. */

export type Job = {
  id: string;
  title: string | null;
  company: string | null;
  location: string | null;
  url: string | null;
  description: string | null;
  source_engine: string | null;
  llm_score: number | null;
  llm_breakdown: string | null;
  prefilter_score: number | null;
};

export type Contact = {
  id: string;
  name: string | null;
  target_company: string | null;
  current_role: string | null;
  current_company: string | null;
  linkedin_url: string | null;
  email: string | null;
  degree_type: string | null;
  warmth_score: number | null;
  warmth_reasons: string[];
  source: string | null;
  outreach_status: string;
};

export type SendHandOff = {
  action: string;
  url: string | null;
  copy_text: string;
  instructions: string;
};

export type Message = {
  id: string;
  contact_id: string | null;
  contact_name: string | null;
  message_type: string | null;
  channel: string | null;
  subject: string | null;
  body: string | null;
  tone: string | null;
  status: string;
  sent_at: string | null;
  send: SendHandOff;
};

export type Application = {
  id: string;
  job_id: string | null;
  company_name: string | null;
  role_title: string | null;
  apply_url: string | null;
  source: string | null;
  applied_via: string | null;
  status: string;
  applied_date: string | null;
  offer_amount: number | null;
  offer_currency: string | null;
  notes: string | null;
  follow_up_due: string | null;
};

export type Reminder = Application & { days_overdue: number; action: string };

export type Stats = {
  total: number;
  by_stage: Record<string, number>;
  applied: number;
  responded: number;
  response_rate: number;
  active: number;
  offers: number;
  by_source: Record<string, { applied: number; responded: number; response_rate: number }>;
  best_source: string | null;
};

export type Profile = {
  personal: { name: string | null; email: string | null; location: string | null };
  skills: Record<string, string[]>;
  experience: { company: string | null; role: string | null }[];
  education: { institution: string | null; degree: string | null }[];
  keywords: string[];
};

export type SetupItem = {
  id: string;
  label: string;
  required: boolean;
  configured: boolean;
  unlocks: string;
  detail: string;
  how: string;
};

export type Setup = { ready: boolean; items: SetupItem[]; embedding_model: string };

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    });
  } catch {
    throw new ApiError("Can't reach the backend. Is it running on port 8000?");
  }

  if (!response.ok) {
    const detail = await response
      .json()
      .then((body) => body?.detail)
      .catch(() => null);
    throw new ApiError(detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

const post = <T,>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });

export const api = {
  getProfile: () => request<Profile>("/api/v1/resume/profile"),

  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Profile>("/api/v1/resume/upload", { method: "POST", body: form });
  },

  listJobs: (limit?: number) =>
    request<{ count: number; jobs: Job[] }>(`/api/v1/jobs${limit ? `?limit=${limit}` : ""}`),

  huntJobs: (searchTerm: string, location: string, topN: number) =>
    post<{ total_found: number; scored_count: number; alert_sent: boolean; jobs: Job[] }>(
      "/api/v1/jobs/hunt",
      { search_term: searchTerm, location, top_n: topN },
    ),

  listReferrals: (company?: string) =>
    request<{ count: number; contacts: Contact[] }>(
      `/api/v1/referrals${company ? `?company=${encodeURIComponent(company)}` : ""}`,
    ),

  findReferrals: (company: string, role?: string) =>
    post<{ company: string; count: number; contacts: Contact[]; manual_search_url: string }>(
      "/api/v1/referrals/find",
      { company, role },
    ),

  listOutreach: (status?: string) =>
    request<{ count: number; messages: Message[] }>(
      `/api/v1/outreach${status ? `?status=${status}` : ""}`,
    ),

  draftOutreach: (contactId: string, jobId?: string) =>
    post<Message>("/api/v1/outreach/draft", { contact_id: contactId, job_id: jobId }),

  editOutreach: (id: string, body: string) =>
    request<Message>(`/api/v1/outreach/${id}`, { method: "PUT", body: JSON.stringify({ body }) }),

  approveOutreach: (id: string) => post<Message>(`/api/v1/outreach/${id}/approve`),
  markOutreachSent: (id: string) => post<Message>(`/api/v1/outreach/${id}/sent`),
  skipOutreach: (id: string) => post<Message>(`/api/v1/outreach/${id}/skip`),

  listApplications: () =>
    request<{ count: number; applications: Application[] }>("/api/v1/applications"),

  trackJob: (jobId: string, appliedVia = "direct") =>
    post<Application>("/api/v1/applications/track", { job_id: jobId, applied_via: appliedVia }),

  moveStage: (id: string, status: string) =>
    post<Application>(`/api/v1/applications/${id}/stage`, { status }),

  reminders: () => request<{ count: number; reminders: Reminder[] }>("/api/v1/applications/reminders"),

  stats: () => request<Stats>("/api/v1/applications/stats"),

  setup: () => request<Setup>("/api/v1/setup"),
};
