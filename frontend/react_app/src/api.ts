export type RuntimeStatus = {
  ai_generation_mode: string;
  llm_enabled: boolean;
  vector_db: string;
  embedding_provider: string;
  auth_mode: string;
  default_tenant_id: string;
};

export type Assessment = {
  id: string;
  status: string;
  human_review_status: string;
  profile: { system_name: string; business_domain?: string; deployment_status?: string };
  risk_classification: { risk_level: string; confidence: number; risk_factors: string[]; reasoning_summary: string };
  gap_analysis: { critical_gaps: unknown[]; medium_gaps: unknown[]; priority_actions: string[] };
  evidence_checklist: { evidence: string; status: string; priority: string; owner: string }[];
};

export type SystemRecord = {
  id: string;
  tenant_id: string;
  name: string;
  business_unit?: string;
  owner?: string;
  deployment_status: string;
  created_at: string;
};

export type RiskItem = {
  id: string;
  title: string;
  severity: string;
  status: string;
  owner: string;
  due_date?: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function headers() {
  const apiKey = import.meta.env.VITE_PLATFORM_API_KEY;
  return {
    "Content-Type": "application/json",
    "X-User": import.meta.env.VITE_PLATFORM_USER || "react-ui",
    "X-User-Role": import.meta.env.VITE_PLATFORM_USER_ROLE || "admin",
    "X-Tenant-ID": import.meta.env.VITE_PLATFORM_TENANT_ID || "default",
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
  };
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: headers() });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  runtime: () => getJson<RuntimeStatus>("/runtime/status"),
  systems: () => getJson<SystemRecord[]>("/systems"),
  assessments: () => getJson<Assessment[]>("/assessments"),
  riskRegister: () => getJson<RiskItem[]>("/risk-register"),
};
