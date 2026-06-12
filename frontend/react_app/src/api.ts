export type RuntimeStatus = {
  ai_generation_mode: string;
  llm_enabled: boolean;
  llm_provider: string;
  vector_db: string;
  embedding_provider: string;
  auth_mode: string;
  api_rate_limit_per_minute: number;
  security_headers_enabled: boolean;
  default_tenant_id: string;
};

export type RuntimeReadiness = {
  ready: boolean;
  checks: Record<string, { ok?: boolean; current?: boolean; mode?: string; provider?: string; error?: string }>;
};

export type RuntimeMetrics = {
  total_requests: number;
  total_errors: number;
  routes: Record<
    string,
    {
      request_count: number;
      error_count: number;
      average_duration_ms: number;
      max_duration_ms: number;
      status_counts: Record<string, number>;
    }
  >;
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

export type Incident = {
  id: string;
  title: string;
  severity: string;
  status: string;
  owner: string;
  regulatory_report_required: boolean;
  detected_at: string;
};

export type ReviewEscalation = {
  assessment_id: string;
  system_name: string;
  risk_level: string;
  escalation_level: string;
  escalation_reason?: string;
  age_hours: number;
};

export type RequirementSearchResult = {
  requirement_id: string;
  title: string;
  source: string;
  category: string;
  summary: string;
  relevance: string;
  source_url?: string;
  jurisdiction?: string;
  document_type?: string;
  authority?: string;
  locator?: string;
  tags: string[];
  retriever?: string;
  reranker?: string;
  score?: number;
  score_breakdown: Record<string, number>;
  rank_reasons: string[];
  matched_terms: string[];
  citation_quality?: string;
  evidence_grade?: string;
};

export type LegalSourceSummary = {
  manifest?: string;
  source_count: number;
  available_count: number;
  complete_count: number;
  ready_for_full_legal_corpus: boolean;
  validation: { ready: boolean; errors: string[]; warnings: string[] };
  sources: {
    id: string;
    title: string;
    jurisdiction: string;
    document_type: string;
    ingestion_status: string;
    available: boolean;
    chunk_count: number;
    coverage_percent?: number;
    parsed_locators: string[];
    missing_required_locators: string[];
    readiness: { ready: boolean; blockers: string[]; warnings: string[]; next_actions: string[] };
  }[];
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
  readiness: () => getJson<RuntimeReadiness>("/runtime/readiness"),
  metrics: () => getJson<RuntimeMetrics>("/runtime/metrics"),
  systems: () => getJson<SystemRecord[]>("/systems"),
  assessments: () => getJson<Assessment[]>("/assessments"),
  riskRegister: () => getJson<RiskItem[]>("/risk-register"),
  incidents: () => getJson<Incident[]>("/incidents"),
  reviewEscalations: () => getJson<ReviewEscalation[]>("/reviews/escalations"),
  requirementSearch: (query: string) =>
    getJson<RequirementSearchResult[]>(`/requirements/search?q=${encodeURIComponent(query)}&top_k=4`),
  legalSources: () => getJson<LegalSourceSummary>("/requirements/legal-sources"),
};
