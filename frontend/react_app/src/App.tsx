import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  Database,
  FileCheck2,
  Layers3,
  Search,
  ShieldCheck,
  Siren,
  Users,
} from "lucide-react";
import { api } from "./api";
import type {
  Assessment,
  Incident,
  RequirementSearchResult,
  ReviewEscalation,
  RiskItem,
  RuntimeMetrics,
  RuntimeReadiness,
  RuntimeStatus,
  SystemRecord,
} from "./api";
import "./styles.css";

type LoadState = {
  runtime?: RuntimeStatus;
  readiness?: RuntimeReadiness;
  metrics?: RuntimeMetrics;
  systems: SystemRecord[];
  assessments: Assessment[];
  risks: RiskItem[];
  incidents: Incident[];
  escalations: ReviewEscalation[];
  ragResults: RequirementSearchResult[];
  error?: string;
};

const riskOrder: Record<string, number> = { unacceptable: 4, high: 3, medium: 2, limited: 1, minimal: 0 };

function metric(label: string, value: string | number, detail: string, icon: React.ReactNode) {
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

function App() {
  const [state, setState] = useState<LoadState>({
    systems: [],
    assessments: [],
    risks: [],
    incidents: [],
    escalations: [],
    ragResults: [],
  });

  useEffect(() => {
    Promise.all([
      api.runtime(),
      api.readiness(),
      api.metrics(),
      api.systems(),
      api.assessments(),
      api.riskRegister(),
      api.incidents(),
      api.reviewEscalations(),
      api.requirementSearch("AI Act human oversight personal data incident reporting"),
    ])
      .then(([runtime, readiness, metrics, systems, assessments, risks, incidents, escalations, ragResults]) =>
        setState({ runtime, readiness, metrics, systems, assessments, risks, incidents, escalations, ragResults })
      )
      .catch((error: Error) => setState((current) => ({ ...current, error: error.message })));
  }, []);

  const summary = useMemo(() => {
    const highRisk = state.assessments.filter((item) => riskOrder[item.risk_classification.risk_level] >= 3);
    const pending = state.assessments.filter((item) => item.human_review_status !== "approved");
    const missingEvidence = state.assessments.flatMap((item) => item.evidence_checklist).filter((item) => item.status === "missing");
    const approvedEvidence = state.assessments
      .flatMap((item) => item.evidence_checklist)
      .filter((item) => item.status === "approved");
    const openRisks = state.risks.filter((item) => item.status !== "closed");
    const openIncidents = state.incidents.filter((item) => !["resolved", "closed"].includes(item.status));
    return { highRisk, pending, missingEvidence, approvedEvidence, openRisks, openIncidents };
  }, [state.assessments, state.risks, state.incidents]);

  const readinessChecks = Object.entries(state.readiness?.checks || {});
  const slowRoutes = Object.entries(state.metrics?.routes || {})
    .sort(([, a], [, b]) => b.average_duration_ms - a.average_duration_ms)
    .slice(0, 4);

  const recentAssessments = [...state.assessments]
    .sort((a, b) => riskOrder[b.risk_classification.risk_level] - riskOrder[a.risk_classification.risk_level])
    .slice(0, 6);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck size={28} />
          <div>
            <strong>AI Governance</strong>
            <span>Compliance operations</span>
          </div>
        </div>
        <nav>
          <a className="active"><Activity size={18} /> Command center</a>
          <a><Layers3 size={18} /> Systems</a>
          <a><FileCheck2 size={18} /> Evidence</a>
          <a><AlertTriangle size={18} /> Risk register</a>
          <a><Siren size={18} /> Incidents</a>
        </nav>
        <div className="runtime">
          <span>Tenant</span>
          <strong>{state.runtime?.default_tenant_id || "default"}</strong>
          <span>Vector</span>
          <strong>{state.runtime?.vector_db || "local"}</strong>
          <span>Embeddings</span>
          <strong>{state.runtime?.embedding_provider || "local_hash"}</strong>
          <span>Readiness</span>
          <strong>{state.readiness?.ready ? "ready" : "checking"}</strong>
        </div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Enterprise AI risk platform</p>
            <h1>Governance command center</h1>
          </div>
          <div className="status">
            {state.readiness?.ready ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
            {state.runtime?.auth_mode === "api_key" ? "Protected API" : "Local mode"}
          </div>
        </header>

        {state.error ? <div className="error">API unavailable: {state.error}</div> : null}

        <section className="metrics-grid">
          {metric("AI systems", state.systems.length, "Inventory scope", <Database size={20} />)}
          {metric("High risk", summary.highRisk.length, "Needs governance focus", <AlertTriangle size={20} />)}
          {metric("Pending reviews", summary.pending.length, "Human approval gate", <Users size={20} />)}
          {metric("Missing evidence", summary.missingEvidence.length, "Audit readiness gap", <FileCheck2 size={20} />)}
          {metric("Open risks", summary.openRisks.length, "Risk register", <Activity size={20} />)}
          {metric("Open incidents", summary.openIncidents.length, "Operational response", <Siren size={20} />)}
          {metric("Escalated reviews", state.escalations.length, "SLA and critical gaps", <AlertTriangle size={20} />)}
          {metric("API requests", state.metrics?.total_requests || 0, "Runtime traffic", <BarChart3 size={20} />)}
          {metric("Evidence approved", summary.approvedEvidence.length, "Audit-ready records", <FileCheck2 size={20} />)}
        </section>

        <section className="workspace">
          <div className="panel wide">
            <div className="panel-title">
              <h2>Assessment queue</h2>
              <span>{recentAssessments.length} prioritized</span>
            </div>
            <div className="table">
              <div className="row head">
                <span>System</span>
                <span>Risk</span>
                <span>Review</span>
                <span>Evidence</span>
              </div>
              {recentAssessments.map((item) => (
                <div className="row" key={item.id}>
                  <span>{item.profile.system_name}</span>
                  <span className={`pill risk-${item.risk_classification.risk_level}`}>{item.risk_classification.risk_level}</span>
                  <span>{item.human_review_status}</span>
                  <span>{item.evidence_checklist.filter((evidence) => evidence.status === "missing").length} missing</span>
                </div>
              ))}
              {recentAssessments.length === 0 ? <div className="empty">No assessments yet.</div> : null}
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">
              <h2>Runtime readiness</h2>
              <span>{state.readiness?.ready ? "Ready" : "Needs attention"}</span>
            </div>
            <div className="check-list">
              {readinessChecks.slice(0, 7).map(([name, check]) => (
                <div className="check-row" key={name}>
                  <span>{name.replace(/_/g, " ")}</span>
                  <strong className={check.ok === false || check.current === false ? "bad" : "good"}>
                    {check.ok === false || check.current === false ? "attention" : "ok"}
                  </strong>
                </div>
              ))}
            </div>
          </div>

          <div className="panel wide">
            <div className="panel-title">
              <h2>RAG retrieval evidence</h2>
              <span>{state.ragResults[0]?.reranker || "metadata reranker"}</span>
            </div>
            <div className="rag-list">
              {state.ragResults.map((item, index) => (
                <article key={item.requirement_id}>
                  <div className="rag-rank">
                    <Search size={16} />
                    <strong>#{index + 1}</strong>
                  </div>
                  <div className="rag-body">
                    <div className="rag-heading">
                      <strong>{item.title}</strong>
                      <span>{item.score?.toFixed(1) || "0.0"}</span>
                    </div>
                    <p>{item.rank_reasons[0] || item.relevance}</p>
                    <div className="rag-meta">
                      <span>{item.jurisdiction || "internal"}</span>
                      <span>{item.document_type || "unknown"}</span>
                      <span>{item.citation_quality || "citation"}</span>
                      <span>{item.evidence_grade || "evidence"}</span>
                    </div>
                  </div>
                </article>
              ))}
              {state.ragResults.length === 0 ? <div className="empty">Retrieval evidence will appear after API traffic.</div> : null}
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">
              <h2>Open risks</h2>
              <span>Register</span>
            </div>
            <div className="risk-list">
              {summary.openRisks.slice(0, 5).map((risk) => (
                <article key={risk.id}>
                  <strong>{risk.title}</strong>
                  <div>
                    <span className={`pill risk-${risk.severity}`}>{risk.severity}</span>
                    <span>{risk.owner}</span>
                  </div>
                </article>
              ))}
              {summary.openRisks.length === 0 ? <div className="empty">No open risks.</div> : null}
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">
              <h2>AI incidents</h2>
              <span>Response</span>
            </div>
            <div className="risk-list">
              {summary.openIncidents.slice(0, 5).map((incident) => (
                <article key={incident.id}>
                  <strong>{incident.title}</strong>
                  <div>
                    <span className={`pill risk-${incident.severity}`}>{incident.severity}</span>
                    <span>{incident.status}</span>
                  </div>
                  <small>{incident.regulatory_report_required ? "Report review required" : incident.owner}</small>
                </article>
              ))}
              {summary.openIncidents.length === 0 ? <div className="empty">No open incidents.</div> : null}
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">
              <h2>Review escalations</h2>
              <span>SLA</span>
            </div>
            <div className="risk-list">
              {state.escalations.slice(0, 5).map((item) => (
                <article key={item.assessment_id}>
                  <strong>{item.system_name}</strong>
                  <div>
                    <span className={`pill risk-${item.risk_level}`}>{item.risk_level}</span>
                    <span>{item.escalation_level}</span>
                  </div>
                  <small>{item.escalation_reason || `${item.age_hours}h in queue`}</small>
                </article>
              ))}
              {state.escalations.length === 0 ? <div className="empty">No escalations.</div> : null}
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">
              <h2>API latency</h2>
              <span>Observed routes</span>
            </div>
            <div className="check-list">
              {slowRoutes.map(([route, item]) => (
                <div className="check-row" key={route}>
                  <span>{route}</span>
                  <strong>
                    <Clock3 size={14} /> {item.average_duration_ms.toFixed(1)} ms
                  </strong>
                </div>
              ))}
              {slowRoutes.length === 0 ? <div className="empty">Metrics will appear after API traffic.</div> : null}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

export default App;
