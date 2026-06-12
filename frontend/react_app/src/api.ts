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

export type LLMProviderOption = {
  id: string;
  label: string;
  configured: boolean;
  model: string;
  base_url: string;
  requires_key: string;
};

export type LLMOptions = {
  default_mode: string;
  default_provider?: string | null;
  default_model?: string | null;
  providers: LLMProviderOption[];
  configured_provider_count: number;
  defaults: {
    timeout_seconds: number;
    max_retries: number;
    max_tokens: number;
    temperature: number;
  };
};

export type RuntimeConfig = {
  active: {
    ai_generation_mode: string;
    llm_provider: string;
    openai_base_url: string;
    openai_model: string;
    openai_timeout_seconds: number;
    openai_max_retries: number;
    openai_max_tokens: number;
    anthropic_base_url: string;
    anthropic_model: string;
    langsmith_tracing: boolean;
    langsmith_project: string;
    vector_db: string;
    qdrant_url: string;
    qdrant_collection: string;
    embedding_provider: string;
    openai_embedding_model: string;
    embedding_dimensions: number;
  };
  secrets: Record<string, { configured: boolean; from_runtime_config: boolean }>;
  providers: LLMProviderOption[];
};

export type RuntimeReadiness = {
  ready: boolean;
  checks: Record<string, { ok?: boolean; current?: boolean; mode?: string; provider?: string; error?: string }>;
};

export type RuntimeMetrics = {
  total_requests: number;
  total_errors: number;
  routes: Record<string, { request_count: number; error_count: number; average_duration_ms: number; max_duration_ms: number }>;
};

export type RuntimePreflight = {
  target: string;
  release_ready: boolean;
  blocker_count: number;
  warning_count: number;
  blockers: { code: string; message: string; check?: string }[];
  warnings: { code: string; message: string; check?: string }[];
  actions: string[];
};

export type LLMUsageSummary = {
  assessment_count: number;
  llm_call_count: number;
  successful_llm_call_count: number;
  failed_llm_call_count: number;
  skipped_llm_call_count: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  total_latency_ms: number;
  average_latency_ms: number;
  estimated_cost_usd?: number;
  providers: string[];
  models: string[];
  prompt_versions: string[];
};

export type Assessment = {
  id: string;
  system_id: string;
  status: string;
  human_review_status: string;
  profile: {
    system_name: string;
    use_case?: string;
    business_domain?: string;
    deployment_status?: string;
    model_provider?: string;
    model_type?: string;
  };
  risk_classification: { risk_level: string; confidence: number; risk_factors: string[]; reasoning_summary: string };
  retrieved_requirements: RequirementSearchResult[];
  mapped_controls: { requirement_id: string; requirement: string; mapped_control: string; control_status: string; evidence_needed: string[] }[];
  gap_analysis: {
    overall_status: string;
    critical_gaps: { gap: string; risk: string; recommended_action: string }[];
    medium_gaps: { gap: string; risk: string; recommended_action: string }[];
    low_gaps: { gap: string; risk: string; recommended_action: string }[];
    priority_actions: string[];
  };
  evidence_checklist: { evidence: string; status: string; priority: string; owner: string }[];
  ai_system_card: { title: string; content_markdown: string; status: string };
  audit_report: { title: string; content_markdown: string; status: string };
  tool_calls: Record<string, unknown>[];
  disclaimer: string;
};

export type SystemRecord = {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  business_unit?: string;
  owner?: string;
  deployment_status: string;
  created_at: string;
};

export type EvidenceRecord = {
  id: string;
  assessment_id: string;
  name: string;
  description: string;
  priority: string;
  owner: string;
  status: string;
  file_url?: string;
  source_system?: string;
  evidence_hash?: string;
  due_date?: string;
  expires_at?: string;
  approved_by?: string;
  review_notes?: string;
};

export type RiskItem = {
  id: string;
  assessment_id: string;
  system_id: string;
  title: string;
  description: string;
  severity: string;
  likelihood: string;
  impact: string;
  status: string;
  owner: string;
  mitigation_plan?: string;
  due_date?: string;
};

export type Incident = {
  id: string;
  system_id: string;
  assessment_id?: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  owner: string;
  regulatory_report_required: boolean;
  detected_at: string;
  impact_summary?: string;
};

export type ReviewQueueItem = {
  assessment_id: string;
  system_id: string;
  system_name: string;
  risk_level: string;
  status: string;
  critical_gap_count: number;
  missing_evidence_count: number;
  age_hours: number;
  escalation_level: string;
  escalation_reason?: string;
};

export type ReviewEscalation = ReviewQueueItem;

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
    readiness: { ready: boolean; blockers: string[]; warnings: string[]; next_actions: string[] };
  }[];
};

export type PolicyExceptionQueueItem = {
  id: string;
  title: string;
  status: string;
  expiry_state: string;
  days_until_expiry?: number;
  action_required: string;
  compensating_control_count: number;
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

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

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: headers(),
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return (await response.text()) as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  runtime: () => request<RuntimeStatus>("GET", "/runtime/status"),
  runtimeConfig: () => request<RuntimeConfig>("GET", "/runtime/config"),
  updateRuntimeConfig: (payload: Record<string, unknown>) => request<RuntimeConfig>("PATCH", "/runtime/config", payload),
  llmOptions: () => request<LLMOptions>("GET", "/runtime/llm-options"),
  readiness: () => request<RuntimeReadiness>("GET", "/runtime/readiness"),
  preflight: () => request<RuntimePreflight>("GET", "/runtime/preflight"),
  metrics: () => request<RuntimeMetrics>("GET", "/runtime/metrics"),
  llmUsage: () => request<LLMUsageSummary>("GET", "/assessments/llm-usage"),
  systems: () => request<SystemRecord[]>("GET", "/systems"),
  createSystem: (payload: Record<string, unknown>) => request<SystemRecord>("POST", "/systems", payload),
  assessSystem: (systemId: string, payload: Record<string, unknown>) => request<Assessment>("POST", `/systems/${systemId}/assess`, payload),
  assessments: () => request<Assessment[]>("GET", "/assessments"),
  assessment: (assessmentId: string) => request<Assessment>("GET", `/assessments/${assessmentId}`),
  evidence: (assessmentId: string) => request<EvidenceRecord[]>("GET", `/evidence/assessments/${assessmentId}`),
  updateEvidence: (evidenceId: string, payload: Record<string, unknown>) => request<EvidenceRecord>("PATCH", `/evidence/items/${evidenceId}`, payload),
  readinessScore: (assessmentId: string) => request<{ score: number; status_counts: Record<string, number> }>("GET", `/evidence/assessments/${assessmentId}/readiness-score`),
  riskRegister: () => request<RiskItem[]>("GET", "/risk-register"),
  syncRisks: (assessmentId: string) => request<RiskItem[]>("POST", `/risk-register/assessments/${assessmentId}/sync`, {}),
  updateRisk: (riskId: string, payload: Record<string, unknown>) => request<RiskItem>("PATCH", `/risk-register/${riskId}`, payload),
  incidents: () => request<Incident[]>("GET", "/incidents"),
  createIncident: (payload: Record<string, unknown>) => request<Incident>("POST", "/incidents", payload),
  updateIncident: (incidentId: string, payload: Record<string, unknown>) => request<Incident>("PATCH", `/incidents/${incidentId}`, payload),
  reviewQueue: () => request<ReviewQueueItem[]>("GET", "/reviews/queue"),
  reviewEscalations: () => request<ReviewEscalation[]>("GET", "/reviews/escalations"),
  reviewAction: (assessmentId: string, action: "approve" | "reject" | "request-more-evidence", payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("POST", `/reviews/${assessmentId}/${action}`, payload),
  requirementSearch: (query: string) => request<RequirementSearchResult[]>("GET", `/requirements/search?q=${encodeURIComponent(query)}&top_k=8`),
  legalSources: () => request<LegalSourceSummary>("GET", "/requirements/legal-sources"),
  expiringExceptions: () => request<PolicyExceptionQueueItem[]>("GET", "/risk-register/exceptions/expiring?within_days=30"),
  reportUrl: (assessmentId: string) => `${API_BASE_URL}/reports/${assessmentId}`,
  cardUrl: (assessmentId: string) => `${API_BASE_URL}/reports/${assessmentId}/system-card`,
  auditPackageUrl: (assessmentId: string) => `${API_BASE_URL}/audit/assessments/${assessmentId}/package.zip`,
};
