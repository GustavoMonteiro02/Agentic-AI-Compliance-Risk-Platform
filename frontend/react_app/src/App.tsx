import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Database,
  FileCheck2,
  FileText,
  Layers3,
  RefreshCw,
  Search,
  ShieldCheck,
  Siren,
  Users,
} from "lucide-react";
import { API_BASE_URL, api } from "./api";
import type {
  Assessment,
  AuditEvent,
  EvidenceRecord,
  Incident,
  LegalSourceSummary,
  LLMOptions,
  LLMUsageSummary,
  RequirementSearchResult,
  ReviewEscalation,
  ReviewQueueItem,
  RiskItem,
  RuntimeConfig,
  RuntimePreflight,
  RuntimeReadiness,
  RuntimeStatus,
  SystemRecord,
} from "./api";
import "./styles.css";

type Page = "overview" | "intake" | "assessments" | "requirements" | "evidence" | "risks" | "incidents" | "reviews" | "history" | "operations";

type LoadState = {
  runtime?: RuntimeStatus;
  runtimeConfig?: RuntimeConfig;
  llmOptions?: LLMOptions;
  readiness?: RuntimeReadiness;
  preflight?: RuntimePreflight;
  llmUsage?: LLMUsageSummary;
  systems: SystemRecord[];
  assessments: Assessment[];
  risks: RiskItem[];
  incidents: Incident[];
  reviewQueue: ReviewQueueItem[];
  escalations: ReviewEscalation[];
  auditEvents: AuditEvent[];
  legalSources?: LegalSourceSummary;
};

const emptyState: LoadState = {
  systems: [],
  assessments: [],
  risks: [],
  incidents: [],
  reviewQueue: [],
  escalations: [],
  auditEvents: [],
};

const riskOrder: Record<string, number> = { critical: 5, unacceptable: 4, high: 3, medium: 2, limited: 1, minimal: 0, low: 0 };

function csv(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function nice(value?: string | number | null) {
  if (value === undefined || value === null || value === "") return "Not set";
  return String(value).replace(/_/g, " ");
}

function App() {
  const [page, setPage] = useState<Page>("overview");
  const [state, setState] = useState<LoadState>(emptyState);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>("");
  const [selectedAssessment, setSelectedAssessment] = useState<Assessment | null>(null);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [requirementQuery, setRequirementQuery] = useState("AI Act human oversight personal data");
  const [requirements, setRequirements] = useState<RequirementSearchResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    setError("");
    const [runtime, runtimeConfig, llmOptions, readiness, preflight, llmUsage, systems, assessments, risks, incidents, reviewQueue, escalations, auditEvents, legalSources] =
      await Promise.all([
        api.runtime(),
        api.runtimeConfig(),
        api.llmOptions(),
        api.readiness(),
        api.preflight(),
        api.llmUsage(),
        api.systems(),
        api.assessments(),
        api.riskRegister(),
        api.incidents(),
        api.reviewQueue(),
        api.reviewEscalations(),
        api.auditEvents(),
        api.legalSources(),
      ]);
    setState({ runtime, runtimeConfig, llmOptions, readiness, preflight, llmUsage, systems, assessments, risks, incidents, reviewQueue, escalations, auditEvents, legalSources });
    if (!selectedAssessmentId && assessments[0]) setSelectedAssessmentId(assessments[0].id);
  };

  useEffect(() => {
    refresh().catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedAssessmentId) {
      setSelectedAssessment(null);
      setEvidence([]);
      return;
    }
    Promise.all([api.assessment(selectedAssessmentId), api.evidence(selectedAssessmentId)])
      .then(([assessment, evidenceItems]) => {
        setSelectedAssessment(assessment);
        setEvidence(evidenceItems);
      })
      .catch((err: Error) => setError(err.message));
  }, [selectedAssessmentId]);

  const summary = useMemo(() => {
    const highRisk = state.assessments.filter((item) => riskOrder[item.risk_classification.risk_level] >= 3);
    const pending = state.assessments.filter((item) => item.human_review_status !== "approved");
    const missingEvidence = state.assessments.flatMap((item) => item.evidence_checklist).filter((item) => item.status === "missing");
    const openRisks = state.risks.filter((item) => item.status !== "closed");
    const openIncidents = state.incidents.filter((item) => !["resolved", "closed"].includes(item.status));
    return { highRisk, pending, missingEvidence, openRisks, openIncidents };
  }, [state]);

  const run = async (fn: () => Promise<void>, success: string) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fn();
      await refresh();
      setNotice(success);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck size={26} />
          <div>
            <strong>AI Governance</strong>
            <span>Compliance Risk Platform</span>
          </div>
        </div>
        <nav>
          <NavButton page="overview" current={page} setPage={setPage} icon={<Activity size={17} />} label="Start here" />
          <NavButton page="intake" current={page} setPage={setPage} icon={<Layers3 size={17} />} label="1. Create & run" />
          <NavButton page="assessments" current={page} setPage={setPage} icon={<FileText size={17} />} label="2. Results" />
          <NavButton page="evidence" current={page} setPage={setPage} icon={<FileCheck2 size={17} />} label="3. Evidence" />
          <NavButton page="risks" current={page} setPage={setPage} icon={<AlertTriangle size={17} />} label="4. Risks" />
          <NavButton page="reviews" current={page} setPage={setPage} icon={<Users size={17} />} label="5. Review" />
          <NavButton page="history" current={page} setPage={setPage} icon={<Clock3 size={17} />} label="History" />
          <NavButton page="requirements" current={page} setPage={setPage} icon={<Search size={17} />} label="Library" />
          <NavButton page="incidents" current={page} setPage={setPage} icon={<Siren size={17} />} label="Incidents" />
          <NavButton page="operations" current={page} setPage={setPage} icon={<Database size={17} />} label="Settings" />
        </nav>
        <div className="runtime">
          <span>Tenant</span>
          <strong>{state.runtime?.default_tenant_id || "default"}</strong>
          <span>API</span>
          <strong>{state.runtime?.auth_mode === "api_key" ? "protected" : "local"}</strong>
          <span>Vector</span>
          <strong>{state.runtime?.vector_db || "local"}</strong>
          <span>Embeddings</span>
          <strong>{state.runtime?.embedding_provider || "local_hash"}</strong>
        </div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Enterprise AI risk platform</p>
            <h1>{titleFor(page)}</h1>
          </div>
          <div className="top-actions">
            <select value={selectedAssessmentId} onChange={(event) => setSelectedAssessmentId(event.target.value)}>
              <option value="">No assessment selected</option>
              {state.assessments.map((assessment) => (
                <option key={assessment.id} value={assessment.id}>
                  {assessment.profile.system_name}
                </option>
              ))}
            </select>
            <button className="secondary" onClick={() => refresh()} disabled={busy}>
              <RefreshCw size={16} /> Refresh
            </button>
          </div>
        </header>

        {notice ? <div className="notice">{notice}</div> : null}
        {error ? <div className="error">{error}</div> : null}
        <WorkflowGuide state={state} currentPage={page} setPage={setPage} />

        {page === "overview" ? <Overview state={state} summary={summary} setPage={setPage} /> : null}
        {page === "intake" ? <Intake state={state} run={run} setSelectedAssessmentId={setSelectedAssessmentId} /> : null}
        {page === "assessments" ? <Assessments assessment={selectedAssessment} state={state} run={run} /> : null}
        {page === "requirements" ? <Requirements query={requirementQuery} setQuery={setRequirementQuery} results={requirements} setResults={setRequirements} run={run} legalSources={state.legalSources} /> : null}
        {page === "evidence" ? <Evidence evidence={evidence} run={run} assessment={selectedAssessment} reload={() => selectedAssessmentId && api.evidence(selectedAssessmentId).then(setEvidence)} /> : null}
        {page === "risks" ? <Risks risks={state.risks} assessment={selectedAssessment} run={run} /> : null}
        {page === "incidents" ? <Incidents incidents={state.incidents} systems={state.systems} assessment={selectedAssessment} run={run} /> : null}
        {page === "reviews" ? <Reviews queue={state.reviewQueue} assessment={selectedAssessment} run={run} /> : null}
        {page === "history" ? <History events={state.auditEvents} setPage={setPage} /> : null}
        {page === "operations" ? <Operations state={state} run={run} /> : null}
      </section>
    </main>
  );
}

function NavButton({ page, current, setPage, icon, label }: { page: Page; current: Page; setPage: (page: Page) => void; icon: React.ReactNode; label: string }) {
  return (
    <button className={current === page ? "active" : ""} onClick={() => setPage(page)}>
      {icon} {label}
    </button>
  );
}

type WorkflowStep = {
  page: Page;
  label: string;
  status: "done" | "active" | "todo" | "attention";
  metric: string;
};

function getWorkflowSteps(state: LoadState): WorkflowStep[] {
  const hasRuntime = Boolean(state.runtime);
  const hasSystems = state.systems.length > 0;
  const hasAssessment = state.assessments.length > 0;
  const missingEvidence = state.assessments.flatMap((item) => item.evidence_checklist).filter((item) => item.status === "missing").length;
  const hasRisks = state.risks.length > 0;
  const pendingReviews = state.assessments.filter((item) => item.human_review_status !== "approved").length;
  return [
    { page: "operations", label: "Runtime", status: hasRuntime && state.readiness?.ready ? "done" : hasRuntime ? "attention" : "active", metric: state.runtime?.llm_provider || "setup" },
    { page: "intake", label: "Create", status: hasSystems ? "done" : "active", metric: `${state.systems.length} systems` },
    { page: "assessments", label: "Assess", status: hasAssessment ? "done" : hasSystems ? "active" : "todo", metric: `${state.assessments.length} runs` },
    { page: "evidence", label: "Evidence", status: !hasAssessment ? "todo" : missingEvidence ? "attention" : "done", metric: `${missingEvidence} missing` },
    { page: "risks", label: "Risks", status: !hasAssessment ? "todo" : hasRisks ? "done" : "active", metric: `${state.risks.length} items` },
    { page: "reviews", label: "Review", status: !hasAssessment ? "todo" : pendingReviews ? "attention" : "done", metric: `${pendingReviews} pending` },
  ];
}

function nextWorkflowPage(steps: WorkflowStep[]): Page {
  return steps.find((step) => step.status === "active" || step.status === "attention")?.page || "assessments";
}

function WorkflowGuide({ state, currentPage, setPage }: { state: LoadState; currentPage: Page; setPage: (page: Page) => void }) {
  const steps = getWorkflowSteps(state);
  const nextPage = nextWorkflowPage(steps);
  return (
    <section className="workflow-band">
      <div className="workflow-head">
        <div>
          <span className="eyebrow">Assessment flow</span>
          <strong>{workflowSummary(steps)}</strong>
        </div>
        <button className="primary compact" onClick={() => setPage(nextPage)}>
          Continue <ArrowRight size={15} />
        </button>
      </div>
      <div className="workflow-steps">
        {steps.map((step, index) => (
          <button
            key={step.page}
            className={`flow-step ${step.status} ${currentPage === step.page ? "selected" : ""}`}
            onClick={() => setPage(step.page)}
          >
            <span className="flow-index">{step.status === "done" ? <CheckCircle2 size={15} /> : index + 1}</span>
            <span>
              <strong>{step.label}</strong>
              <small>{step.metric}</small>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}

function workflowSummary(steps: WorkflowStep[]) {
  const next = steps.find((step) => step.status === "active" || step.status === "attention");
  if (!next) return "Assessment package ready";
  return `${next.label} is next`;
}

function titleFor(page: Page) {
  return {
    overview: "Governance command center",
    intake: "Create assessment",
    assessments: "Assessment workspace",
    requirements: "Requirements search",
    evidence: "Evidence center",
    risks: "Risk register",
    incidents: "Incident response",
    reviews: "Human review",
    history: "Activity history",
    operations: "Runtime operations",
  }[page];
}

function Metric({ label, value, detail, icon }: { label: string; value: string | number; detail: string; icon: React.ReactNode }) {
  return (
    <section className="metric">
      <div className="metric-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </section>
  );
}

function Overview({
  state,
  summary,
  setPage,
}: {
  state: LoadState;
  summary: {
    highRisk: Assessment[];
    pending: Assessment[];
    missingEvidence: { evidence: string; status: string; priority: string; owner: string }[];
    openRisks: RiskItem[];
    openIncidents: Incident[];
  };
  setPage: (page: Page) => void;
}) {
  const steps = getWorkflowSteps(state);
  const nextPage = nextWorkflowPage(steps);
  return (
    <>
      <section className="metrics-grid">
        <Metric label="AI systems" value={state.systems.length} detail="Inventory records" icon={<Database size={20} />} />
        <Metric label="High risk" value={summary.highRisk.length} detail="Needs governance focus" icon={<AlertTriangle size={20} />} />
        <Metric label="Pending reviews" value={summary.pending.length} detail="Human approval queue" icon={<Users size={20} />} />
        <Metric label="Missing evidence" value={summary.missingEvidence.length} detail="Audit readiness gap" icon={<FileCheck2 size={20} />} />
        <Metric label="Open risks" value={summary.openRisks.length} detail="Risk register" icon={<Activity size={20} />} />
        <Metric label="Open incidents" value={summary.openIncidents.length} detail="Response workflow" icon={<Siren size={20} />} />
        <Metric label="LLM tokens" value={state.llmUsage?.total_tokens || 0} detail={`${state.llmUsage?.llm_call_count || 0} calls`} icon={<BarChart3 size={20} />} />
        <Metric label="Preflight" value={state.preflight?.release_ready ? "Ready" : "Review"} detail={`${state.preflight?.warning_count || 0} warnings`} icon={<ShieldCheck size={20} />} />
      </section>
      <section className="operator-lane">
        <div>
          <span className="eyebrow">Current handoff</span>
          <h2>{workflowSummary(steps)}</h2>
        </div>
        <div className="operator-actions">
          <button className="primary" onClick={() => setPage(nextPage)}>
            Open next workspace <ArrowRight size={16} />
          </button>
          <button className="secondary" onClick={() => setPage("operations")}>
            <ClipboardCheck size={16} /> Check runtime
          </button>
        </div>
      </section>
      <section className="action-grid">
        <button className="action-card" onClick={() => setPage("intake")}>
          <Layers3 size={20} />
          <span>
            <strong>Create and run an assessment</strong>
            <small>Register the AI system and immediately generate risk, gaps, evidence, and reports.</small>
          </span>
          <ArrowRight size={16} />
        </button>
        <button className="action-card" onClick={() => setPage("assessments")}>
          <FileText size={20} />
          <span>
            <strong>Open assessment results</strong>
            <small>Read the risk decision, mapped controls, gap analysis, and export audit documents.</small>
          </span>
          <ArrowRight size={16} />
        </button>
        <button className="action-card" onClick={() => setPage("reviews")}>
          <Users size={20} />
          <span>
            <strong>Finish human review</strong>
            <small>Approve, reject, or request more evidence for the selected assessment.</small>
          </span>
          <ArrowRight size={16} />
        </button>
      </section>
      <section className="grid-2">
        <Panel title="Recent assessments" meta={`${state.assessments.length} total`}>
          <Table headers={["System", "Risk", "Review", "Evidence"]}>
            {state.assessments.slice(0, 8).map((item) => (
              <div className="tr" key={item.id}>
                <span>{item.profile.system_name}</span>
                <span className={`pill risk-${item.risk_classification.risk_level}`}>{item.risk_classification.risk_level}</span>
                <span>{item.human_review_status}</span>
                <span>{item.evidence_checklist.filter((e) => e.status === "missing").length} missing</span>
              </div>
            ))}
          </Table>
        </Panel>
        <Panel title="Runtime readiness" meta={state.readiness?.ready ? "Ready" : "Needs attention"}>
          <KeyValues values={Object.entries(state.readiness?.checks || {}).slice(0, 8).map(([key, value]) => [key.replace(/_/g, " "), value.ok === false || value.current === false ? "attention" : "ok"])} />
        </Panel>
        <Panel title="Recent history" meta={`${state.auditEvents.length} persisted events`}>
          <Timeline events={state.auditEvents.slice(0, 8)} />
        </Panel>
      </section>
    </>
  );
}

function Intake({ state, run, setSelectedAssessmentId }: { state: LoadState; run: (fn: () => Promise<void>, success: string) => Promise<void>; setSelectedAssessmentId: (id: string) => void }) {
  const defaultProvider = state.llmOptions?.providers[0];
  const [form, setForm] = useState({
    name: "Recruitment CV Screening Assistant",
    business_unit: "People Operations",
    owner: "Head of Talent",
    technical_owner: "AI Engineering Lead",
    deployment_status: "production",
    users_affected: "job candidates",
    data_types: "CVs, resumes, embeddings, candidate fit scores",
    model_provider: defaultProvider?.label || "Local deterministic workflow",
    model_type: "LLM-assisted workflow",
    decision_impact: "recommendation",
    autonomy_level: "human-in-the-loop",
    human_oversight_process: "Recruiters review AI rankings before any hiring decision.",
    description: "AI assistant in HR analyzes CVs, ranks candidates, stores embeddings, and produces recommendations for recruiters. Human reviewers make final decisions.",
    generation_mode: defaultProvider ? "llm" : "deterministic",
    llm_provider: defaultProvider?.id || "",
    model: defaultProvider?.model || "",
  });
  const update = (key: string, value: string) => setForm((current) => ({ ...current, [key]: value }));
  const providers = state.llmOptions?.providers || [];

  return (
    <form
      className="form-grid"
      onSubmit={(event) => {
        event.preventDefault();
        run(async () => {
          const system = await api.createSystem({
            name: form.name,
            description: form.description,
            business_unit: form.business_unit,
            owner: form.owner,
            technical_owner: form.technical_owner,
            deployment_status: form.deployment_status,
            users_affected: csv(form.users_affected),
            data_types: csv(form.data_types),
            model_provider: form.model_provider,
            model_type: form.model_type,
            decision_impact: form.decision_impact,
            autonomy_level: form.autonomy_level,
            human_oversight_process: form.human_oversight_process,
            external_users_affected: true,
          });
          const assessment = await api.assessSystem(system.id, {
            llm_config: {
              ai_generation_mode: form.generation_mode,
              llm_provider: form.generation_mode === "llm" ? form.llm_provider : undefined,
              model: form.generation_mode === "llm" ? form.model : undefined,
            },
          });
          setSelectedAssessmentId(assessment.id);
        }, "Assessment created and queued for review.");
      }}
    >
      <Panel title="System profile" meta="Required">
        <Field label="System name" value={form.name} onChange={(value) => update("name", value)} />
        <Field label="Business unit" value={form.business_unit} onChange={(value) => update("business_unit", value)} />
        <Field label="Owner" value={form.owner} onChange={(value) => update("owner", value)} />
        <Field label="Technical owner" value={form.technical_owner} onChange={(value) => update("technical_owner", value)} />
        <Field label="Users affected" value={form.users_affected} onChange={(value) => update("users_affected", value)} />
        <Field label="Data types" value={form.data_types} onChange={(value) => update("data_types", value)} />
      </Panel>
      <Panel title="Assessment configuration" meta="Per run">
        <Field label="Model provider" value={form.model_provider} onChange={(value) => update("model_provider", value)} />
        <Field label="Model type" value={form.model_type} onChange={(value) => update("model_type", value)} />
        <Select label="Deployment" value={form.deployment_status} options={["prototype", "internal", "production", "external"]} onChange={(value) => update("deployment_status", value)} />
        <Select label="Generation mode" value={form.generation_mode} options={providers.length ? ["deterministic", "llm"] : ["deterministic"]} onChange={(value) => update("generation_mode", value)} />
        {form.generation_mode === "llm" ? (
          <>
            <Select label="LLM provider" value={form.llm_provider} options={providers.map((p) => p.id)} onChange={(value) => {
              const provider = providers.find((item) => item.id === value);
              setForm((current) => ({ ...current, llm_provider: value, model: provider?.model || current.model }));
            }} />
            <Field label="Model" value={form.model} onChange={(value) => update("model", value)} />
          </>
        ) : (
          <p className="muted">Deterministic mode uses local rules and no paid LLM calls.</p>
        )}
      </Panel>
      <Panel title="Use case" meta="Governance context">
        <Select label="Decision impact" value={form.decision_impact} options={["recommendation", "low", "medium", "high"]} onChange={(value) => update("decision_impact", value)} />
        <Select label="Autonomy" value={form.autonomy_level} options={["human-in-the-loop", "human-on-the-loop", "automated", "unknown"]} onChange={(value) => update("autonomy_level", value)} />
        <TextArea label="Human oversight" value={form.human_oversight_process} onChange={(value) => update("human_oversight_process", value)} />
        <TextArea label="Description" value={form.description} onChange={(value) => update("description", value)} />
        <button className="primary" type="submit">Create and assess</button>
      </Panel>
    </form>
  );
}

function Assessments({ assessment, state, run }: { assessment: Assessment | null; state: LoadState; run: (fn: () => Promise<void>, success: string) => Promise<void> }) {
  if (!assessment) return <Empty text="Create or select an assessment." />;
  return (
    <section className="grid-2">
      <Panel title={assessment.profile.system_name} meta={assessment.human_review_status}>
        <div className="split">
          <span className={`pill risk-${assessment.risk_classification.risk_level}`}>{assessment.risk_classification.risk_level}</span>
          <strong>{Math.round(assessment.risk_classification.confidence * 100)}% confidence</strong>
        </div>
        <p>{assessment.risk_classification.reasoning_summary}</p>
        <KeyValues values={[["Status", assessment.status], ["Deployment", nice(assessment.profile.deployment_status)], ["Provider", nice(assessment.profile.model_provider)], ["Model type", nice(assessment.profile.model_type)]]} />
      </Panel>
      <Panel title="Exports and actions" meta="Audit handoff">
        <div className="button-row">
          <a className="secondary" href={api.cardUrl(assessment.id)} target="_blank">System card</a>
          <a className="secondary" href={api.reportUrl(assessment.id)} target="_blank">Audit report</a>
          <a className="secondary" href={api.auditPackageUrl(assessment.id)} target="_blank">Audit package ZIP</a>
          <button className="secondary" onClick={() => run(() => api.syncRisks(assessment.id).then(() => undefined), "Risks synced from assessment.")}>Sync risks</button>
        </div>
        <p className="muted">{assessment.disclaimer}</p>
      </Panel>
      <Panel title="Mapped controls" meta={`${assessment.mapped_controls.length} controls`}>
        <Table headers={["Requirement", "Control", "Status"]}>
          {assessment.mapped_controls.map((control) => (
            <div className="tr" key={control.requirement_id}>
              <span>{control.requirement}</span>
              <span>{control.mapped_control}</span>
              <span>{control.control_status}</span>
            </div>
          ))}
        </Table>
      </Panel>
      <Panel title="Gap analysis" meta={assessment.gap_analysis.overall_status}>
        {[...assessment.gap_analysis.critical_gaps, ...assessment.gap_analysis.medium_gaps, ...assessment.gap_analysis.low_gaps].map((gap) => (
          <article className="list-item" key={gap.gap}>
            <strong>{gap.gap}</strong>
            <p>{gap.recommended_action}</p>
          </article>
        ))}
      </Panel>
    </section>
  );
}

function Requirements({ query, setQuery, results, setResults, run, legalSources }: { query: string; setQuery: (value: string) => void; results: RequirementSearchResult[]; setResults: (items: RequirementSearchResult[]) => void; run: (fn: () => Promise<void>, success: string) => Promise<void>; legalSources?: LegalSourceSummary }) {
  return (
    <section className="grid-2">
      <Panel title="Search regulatory requirements" meta="RAG">
        <div className="inline-form">
          <input value={query} onChange={(event) => setQuery(event.target.value)} />
          <button className="primary" onClick={() => run(async () => setResults(await api.requirementSearch(query)), "Requirements search complete.")}>Search</button>
        </div>
        <div className="rag-list">
          {results.map((item) => <RequirementCard item={item} key={item.requirement_id} />)}
        </div>
      </Panel>
      <Panel title="Legal source readiness" meta={legalSources?.ready_for_full_legal_corpus ? "Ready" : "Partial"}>
        {(legalSources?.sources || []).map((source) => (
          <article className="list-item" key={source.id}>
            <strong>{source.title}</strong>
            <p>{source.chunk_count} chunks, {source.ingestion_status}</p>
          </article>
        ))}
      </Panel>
    </section>
  );
}

function Evidence({ evidence, assessment, run, reload }: { evidence: EvidenceRecord[]; assessment: Assessment | null; run: (fn: () => Promise<void>, success: string) => Promise<void>; reload: () => Promise<void> | false | "" }) {
  if (!assessment) return <Empty text="Select an assessment to manage evidence." />;
  return (
    <Panel title="Evidence center" meta={`${evidence.length} records`}>
      <div className="cards">
        {evidence.map((item) => <EvidenceEditor key={item.id} item={item} run={run} reload={reload} />)}
      </div>
    </Panel>
  );
}

function EvidenceEditor({ item, run, reload }: { item: EvidenceRecord; run: (fn: () => Promise<void>, success: string) => Promise<void>; reload: () => Promise<void> | false | "" }) {
  const [status, setStatus] = useState(item.status);
  const [owner, setOwner] = useState(item.owner);
  const [notes, setNotes] = useState(item.review_notes || item.description || "");
  return (
    <article className="card">
      <strong>{item.name}</strong>
      <p>{item.description || "No notes yet."}</p>
      <Select label="Status" value={status} options={["missing", "partial", "generated", "uploaded", "approved", "rejected"]} onChange={setStatus} />
      <Field label="Owner" value={owner} onChange={setOwner} />
      <TextArea label="Review notes" value={notes} onChange={setNotes} />
      <button className="secondary" onClick={() => run(async () => { await api.updateEvidence(item.id, { status, owner, review_notes: notes, approved_by: status === "approved" ? "React reviewer" : undefined }); await reload(); }, "Evidence updated.")}>Update evidence</button>
    </article>
  );
}

function Risks({ risks, assessment, run }: { risks: RiskItem[]; assessment: Assessment | null; run: (fn: () => Promise<void>, success: string) => Promise<void> }) {
  return (
    <Panel title="Risk register" meta={`${risks.length} risks`}>
      {assessment ? <button className="primary" onClick={() => run(() => api.syncRisks(assessment.id).then(() => undefined), "Risks synced.")}>Sync active assessment</button> : null}
      <div className="cards">
        {risks.map((risk) => <RiskEditor key={risk.id} risk={risk} run={run} />)}
      </div>
    </Panel>
  );
}

function RiskEditor({ risk, run }: { risk: RiskItem; run: (fn: () => Promise<void>, success: string) => Promise<void> }) {
  const [status, setStatus] = useState(risk.status);
  const [plan, setPlan] = useState(risk.mitigation_plan || "");
  return (
    <article className="card">
      <div className="split"><strong>{risk.title}</strong><span className={`pill risk-${risk.severity}`}>{risk.severity}</span></div>
      <p>{risk.description}</p>
      <Select label="Status" value={status} options={["open", "mitigating", "accepted", "closed"]} onChange={setStatus} />
      <TextArea label="Mitigation plan" value={plan} onChange={setPlan} />
      <button className="secondary" onClick={() => run(() => api.updateRisk(risk.id, { status, mitigation_plan: plan }).then(() => undefined), "Risk updated.")}>Update risk</button>
    </article>
  );
}

function Incidents({ incidents, systems, assessment, run }: { incidents: Incident[]; systems: SystemRecord[]; assessment: Assessment | null; run: (fn: () => Promise<void>, success: string) => Promise<void> }) {
  const [title, setTitle] = useState("Model output incident");
  const [description, setDescription] = useState("Unexpected or harmful model output requires triage and audit review.");
  const systemId = assessment?.system_id || systems[0]?.id || "";
  return (
    <section className="grid-2">
      <Panel title="Create incident" meta="Operational response">
        <Field label="Title" value={title} onChange={setTitle} />
        <TextArea label="Description" value={description} onChange={setDescription} />
        <button className="primary" disabled={!systemId} onClick={() => run(() => api.createIncident({ system_id: systemId, assessment_id: assessment?.id, title, description, severity: "medium", owner: "AI Operations" }).then(() => undefined), "Incident created.")}>Create incident</button>
      </Panel>
      <Panel title="Incident queue" meta={`${incidents.length} records`}>
        {incidents.map((incident) => (
          <article className="list-item" key={incident.id}>
            <div className="split"><strong>{incident.title}</strong><span className={`pill risk-${incident.severity}`}>{incident.severity}</span></div>
            <p>{incident.status} - {incident.owner}</p>
          </article>
        ))}
      </Panel>
    </section>
  );
}

function Reviews({ queue, assessment, run }: { queue: ReviewQueueItem[]; assessment: Assessment | null; run: (fn: () => Promise<void>, success: string) => Promise<void> }) {
  const [notes, setNotes] = useState("Reviewed in React console. Evidence and risk register checked.");
  return (
    <section className="grid-2">
      <Panel title="Active assessment review" meta={assessment?.human_review_status || "none"}>
        {assessment ? (
          <>
            <TextArea label="Reviewer notes" value={notes} onChange={setNotes} />
            <div className="button-row">
              <button className="primary" onClick={() => run(() => api.reviewAction(assessment.id, "approve", { reviewer: "React reviewer", notes }).then(() => undefined), "Assessment approved.")}>Approve</button>
              <button className="secondary" onClick={() => run(() => api.reviewAction(assessment.id, "request-more-evidence", { reviewer: "React reviewer", notes }).then(() => undefined), "More evidence requested.")}>Request evidence</button>
              <button className="danger" onClick={() => run(() => api.reviewAction(assessment.id, "reject", { reviewer: "React reviewer", notes }).then(() => undefined), "Assessment rejected.")}>Reject</button>
            </div>
          </>
        ) : <Empty text="Select an assessment to review." />}
      </Panel>
      <Panel title="Review queue" meta={`${queue.length} items`}>
        {queue.map((item) => (
          <article className="list-item" key={item.assessment_id}>
            <div className="split"><strong>{item.system_name}</strong><span className={`pill risk-${item.risk_level}`}>{item.risk_level}</span></div>
            <p>{item.missing_evidence_count} missing evidence, {item.critical_gap_count} critical gaps</p>
          </article>
        ))}
      </Panel>
    </section>
  );
}

function History({ events, setPage }: { events: AuditEvent[]; setPage: (page: Page) => void }) {
  return (
    <section className="grid-2">
      <Panel title="Persistent activity history" meta={`${events.length} latest events`}>
        <Timeline events={events} />
      </Panel>
      <Panel title="What is stored" meta="Audit trail">
        <div className="key-values">
          <div><span>System creation</span><strong>persisted</strong></div>
          <div><span>Assessment runs</span><strong>persisted</strong></div>
          <div><span>Evidence updates</span><strong>persisted</strong></div>
          <div><span>Risk/review/incident actions</span><strong>persisted</strong></div>
        </div>
        <div className="button-row">
          <button className="secondary" onClick={() => setPage("intake")}>Create new assessment</button>
          <button className="secondary" onClick={() => setPage("assessments")}>Open results</button>
        </div>
      </Panel>
    </section>
  );
}

function Timeline({ events }: { events: AuditEvent[] }) {
  if (!events.length) return <Empty text="No persisted activity yet. Create and run an assessment to start the history." />;
  return (
    <div className="timeline">
      {events.map((event) => (
        <article className="timeline-item" key={event.id}>
          <span className="timeline-dot" />
          <div>
            <div className="split">
              <strong>{actionLabel(event.action)}</strong>
              <small>{formatDateTime(event.created_at)}</small>
            </div>
            <p>{eventSummary(event)}</p>
            <div className="tag-row">
              <span>{event.actor}</span>
              <span>{event.resource_type}</span>
              {event.assessment_id ? <span>assessment</span> : null}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function Operations({ state, run }: { state: LoadState; run: (fn: () => Promise<void>, success: string) => Promise<void> }) {
  return (
    <section className="grid-2">
      <Panel title="Runtime" meta={state.readiness?.ready ? "Ready" : "Attention"}>
        <KeyValues values={[["API base", API_BASE_URL], ["Generation", state.runtime?.ai_generation_mode || ""], ["LLM provider", state.runtime?.llm_provider || ""], ["Vector DB", state.runtime?.vector_db || ""], ["Embedding provider", state.runtime?.embedding_provider || ""]]} />
      </Panel>
      <ProviderSettings config={state.runtimeConfig} run={run} />
      <Panel title="Configured LLMs" meta={`${state.llmOptions?.configured_provider_count || 0} available`}>
        {(state.llmOptions?.providers || []).map((provider) => (
          <article className="list-item" key={provider.id}>
            <strong>{provider.label}</strong>
            <p>{provider.model} - {provider.base_url}</p>
          </article>
        ))}
        {!state.llmOptions?.providers.length ? <Empty text="No live LLM provider configured. Deterministic mode is available." /> : null}
      </Panel>
      <Panel title="Release preflight" meta={`${state.preflight?.warning_count || 0} warnings`}>
        {[...(state.preflight?.blockers || []), ...(state.preflight?.warnings || [])].map((item) => (
          <article className="list-item" key={item.code}>
            <strong>{item.code}</strong>
            <p>{item.message}</p>
          </article>
        ))}
      </Panel>
      <Panel title="LLM usage" meta={`${state.llmUsage?.llm_call_count || 0} calls`}>
        <KeyValues values={[["Prompt tokens", state.llmUsage?.prompt_tokens || 0], ["Completion tokens", state.llmUsage?.completion_tokens || 0], ["Skipped calls", state.llmUsage?.skipped_llm_call_count || 0], ["Providers", state.llmUsage?.providers.join(", ") || "none"]]} />
      </Panel>
    </section>
  );
}

function ProviderSettings({ config, run }: { config?: RuntimeConfig; run: (fn: () => Promise<void>, success: string) => Promise<void> }) {
  const active = config?.active;
  const [form, setForm] = useState({
    ai_generation_mode: active?.ai_generation_mode || "deterministic",
    llm_provider: active?.llm_provider || "openai_compatible",
    openai_base_url: active?.openai_base_url || "http://ollama:11434/v1",
    openai_model: active?.openai_model || "llama3.2:3b",
    openai_api_key: "",
    anthropic_base_url: active?.anthropic_base_url || "https://api.anthropic.com/v1",
    anthropic_model: active?.anthropic_model || "claude-3-5-sonnet-latest",
    anthropic_api_key: "",
    openai_timeout_seconds: String(active?.openai_timeout_seconds || 60),
    openai_max_retries: String(active?.openai_max_retries || 2),
    openai_max_tokens: String(active?.openai_max_tokens || 2000),
    embedding_provider: active?.embedding_provider || "local_hash",
    embedding_dimensions: String(active?.embedding_dimensions || 128),
    vector_db: active?.vector_db || "qdrant",
    qdrant_url: active?.qdrant_url || "http://qdrant:6333",
    qdrant_collection: active?.qdrant_collection || "ai_governance_requirements",
    langsmith_tracing: active?.langsmith_tracing ? "true" : "false",
    langsmith_project: active?.langsmith_project || "ai-governance-compliance-platform",
    langsmith_api_key: "",
  });

  useEffect(() => {
    if (!active) return;
    setForm((current) => ({
      ...current,
      ai_generation_mode: active.ai_generation_mode,
      llm_provider: active.llm_provider,
      openai_base_url: active.openai_base_url,
      openai_model: active.openai_model,
      anthropic_base_url: active.anthropic_base_url,
      anthropic_model: active.anthropic_model,
      openai_timeout_seconds: String(active.openai_timeout_seconds),
      openai_max_retries: String(active.openai_max_retries),
      openai_max_tokens: String(active.openai_max_tokens),
      embedding_provider: active.embedding_provider,
      embedding_dimensions: String(active.embedding_dimensions),
      vector_db: active.vector_db,
      qdrant_url: active.qdrant_url,
      qdrant_collection: active.qdrant_collection,
      langsmith_tracing: active.langsmith_tracing ? "true" : "false",
      langsmith_project: active.langsmith_project,
    }));
  }, [active]);

  const update = (key: string, value: string) => setForm((current) => ({ ...current, [key]: value }));
  const selectedProvider = form.llm_provider;
  const providerConfigured =
    selectedProvider === "anthropic"
      ? Boolean(form.anthropic_api_key || config?.secrets.anthropic_api_key?.configured)
      : Boolean(form.openai_api_key || config?.secrets.openai_api_key?.configured);

  return (
    <Panel title="Provider settings" meta={providerConfigured ? "Configured" : "Needs key"}>
      <div className="settings-stack">
        <Select label="Generation mode" value={form.ai_generation_mode} options={["deterministic", "llm"]} onChange={(value) => update("ai_generation_mode", value)} />
        <Select label="Provider" value={form.llm_provider} options={["openai_compatible", "openai", "anthropic"]} onChange={(value) => {
          const preset = value === "openai" ? { openai_base_url: "https://api.openai.com/v1", openai_model: "gpt-4.1-mini" } : value === "openai_compatible" ? { openai_base_url: form.openai_base_url || "http://ollama:11434/v1", openai_model: form.openai_model || "llama3.2:3b" } : {};
          setForm((current) => ({ ...current, ...preset, llm_provider: value }));
        }} />
        {selectedProvider === "anthropic" ? (
          <>
            <Field label="Anthropic base URL" value={form.anthropic_base_url} onChange={(value) => update("anthropic_base_url", value)} />
            <Field label="Anthropic model" value={form.anthropic_model} onChange={(value) => update("anthropic_model", value)} />
            <SecretField label={config?.secrets.anthropic_api_key?.configured ? "Anthropic API key configured" : "Anthropic API key"} value={form.anthropic_api_key} onChange={(value) => update("anthropic_api_key", value)} />
          </>
        ) : (
          <>
            <Field label={selectedProvider === "openai_compatible" ? "OpenAI-compatible base URL" : "OpenAI base URL"} value={form.openai_base_url} onChange={(value) => update("openai_base_url", value)} />
            <Field label="Model" value={form.openai_model} onChange={(value) => update("openai_model", value)} />
            <SecretField label={config?.secrets.openai_api_key?.configured ? "API key configured" : "API key"} value={form.openai_api_key} onChange={(value) => update("openai_api_key", value)} />
          </>
        )}
        <div className="mini-grid">
          <Field label="Timeout seconds" value={form.openai_timeout_seconds} onChange={(value) => update("openai_timeout_seconds", value)} />
          <Field label="Max retries" value={form.openai_max_retries} onChange={(value) => update("openai_max_retries", value)} />
          <Field label="Max tokens" value={form.openai_max_tokens} onChange={(value) => update("openai_max_tokens", value)} />
        </div>
        <div className="mini-grid">
          <Select label="Vector DB" value={form.vector_db} options={["qdrant", "local", "pinecone"]} onChange={(value) => update("vector_db", value)} />
          <Select label="Embeddings" value={form.embedding_provider} options={["local_hash", "openai"]} onChange={(value) => update("embedding_provider", value)} />
          <Field label="Embedding dimensions" value={form.embedding_dimensions} onChange={(value) => update("embedding_dimensions", value)} />
        </div>
        <Field label="Qdrant URL" value={form.qdrant_url} onChange={(value) => update("qdrant_url", value)} />
        <Field label="Qdrant collection" value={form.qdrant_collection} onChange={(value) => update("qdrant_collection", value)} />
        <div className="mini-grid">
          <Select label="LangSmith tracing" value={form.langsmith_tracing} options={["false", "true"]} onChange={(value) => update("langsmith_tracing", value)} />
          <Field label="LangSmith project" value={form.langsmith_project} onChange={(value) => update("langsmith_project", value)} />
        </div>
        <SecretField label={config?.secrets.langsmith_api_key?.configured ? "LangSmith key configured" : "LangSmith API key"} value={form.langsmith_api_key} onChange={(value) => update("langsmith_api_key", value)} />
        <button
          className="primary"
          onClick={() => run(async () => {
            const payload: Record<string, unknown> = {
              ai_generation_mode: form.ai_generation_mode,
              llm_provider: form.llm_provider,
              openai_base_url: form.openai_base_url,
              openai_model: form.openai_model,
              anthropic_base_url: form.anthropic_base_url,
              anthropic_model: form.anthropic_model,
              openai_timeout_seconds: Number(form.openai_timeout_seconds),
              openai_max_retries: Number(form.openai_max_retries),
              openai_max_tokens: Number(form.openai_max_tokens),
              embedding_provider: form.embedding_provider,
              embedding_dimensions: Number(form.embedding_dimensions),
              vector_db: form.vector_db,
              qdrant_url: form.qdrant_url,
              qdrant_collection: form.qdrant_collection,
              langsmith_tracing: form.langsmith_tracing === "true",
              langsmith_project: form.langsmith_project,
            };
            if (form.openai_api_key) payload.openai_api_key = form.openai_api_key;
            if (!form.openai_api_key && form.llm_provider === "openai_compatible" && form.openai_base_url.includes("ollama") && !config?.secrets.openai_api_key?.configured) {
              payload.openai_api_key = "ollama";
            }
            if (form.anthropic_api_key) payload.anthropic_api_key = form.anthropic_api_key;
            if (form.langsmith_api_key) payload.langsmith_api_key = form.langsmith_api_key;
            await api.updateRuntimeConfig(payload);
          }, "Runtime provider configuration saved.")}
        >
          Save provider config
        </button>
      </div>
    </Panel>
  );
}

function RequirementCard({ item }: { item: RequirementSearchResult }) {
  return (
    <article className="list-item">
      <div className="split"><strong>{item.title}</strong><span>{item.score?.toFixed(1) || "0.0"}</span></div>
      <p>{item.summary}</p>
      <div className="tag-row">
        <span>{item.jurisdiction || "internal"}</span>
        <span>{item.document_type || "policy"}</span>
        <span>{item.citation_quality || "citation"}</span>
      </div>
    </article>
  );
}

function Panel({ title, meta, children }: { title: string; meta?: string; children: React.ReactNode }) {
  return (
    <section className="panel">
      <div className="panel-title"><h2>{title}</h2>{meta ? <span>{meta}</span> : null}</div>
      {children}
    </section>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label>{label}<input value={value} onChange={(event) => onChange(event.target.value)} /></label>;
}

function SecretField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label>{label}<input type="password" value={value} placeholder="Leave blank to keep existing value" onChange={(event) => onChange(event.target.value)} /></label>;
}

function TextArea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label>{label}<textarea value={value} onChange={(event) => onChange(event.target.value)} /></label>;
}

function Select({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return <label>{label}<select value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option} value={option}>{nice(option)}</option>)}</select></label>;
}

function Table({ headers, children }: { headers: string[]; children: React.ReactNode }) {
  return <div className="table"><div className="tr head">{headers.map((header) => <span key={header}>{header}</span>)}</div>{children}</div>;
}

function KeyValues({ values }: { values: [string, string | number][] }) {
  return <div className="key-values">{values.map(([key, value]) => <div key={key}><span>{key}</span><strong>{nice(value)}</strong></div>)}</div>;
}

function Empty({ text }: { text: string }) {
  return <div className="empty">{text}</div>;
}

function actionLabel(action: string) {
  return action.replace(/\./g, " ").replace(/_/g, " ");
}

function eventSummary(event: AuditEvent) {
  const details = event.details_json || {};
  const name = typeof details.system_name === "string" ? details.system_name : typeof details.name === "string" ? details.name : "";
  const risk = typeof details.risk_level === "string" ? ` Risk: ${details.risk_level}.` : "";
  const status = typeof details.status === "string" ? ` Status: ${details.status}.` : "";
  if (name) return `${name}.${risk}${status}`.trim();
  return `${nice(event.resource_id || event.assessment_id || event.resource_type)}.${risk}${status}`.trim();
}

function formatDateTime(value: string) {
  if (!value) return "";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

export default App;
