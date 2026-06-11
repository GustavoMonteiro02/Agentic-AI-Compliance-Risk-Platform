import React, { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, Database, FileCheck2, Layers3, ShieldCheck, Users } from "lucide-react";
import { api, Assessment, RiskItem, RuntimeStatus, SystemRecord } from "./api";
import "./styles.css";

type LoadState = {
  runtime?: RuntimeStatus;
  systems: SystemRecord[];
  assessments: Assessment[];
  risks: RiskItem[];
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
  const [state, setState] = useState<LoadState>({ systems: [], assessments: [], risks: [] });

  useEffect(() => {
    Promise.all([api.runtime(), api.systems(), api.assessments(), api.riskRegister()])
      .then(([runtime, systems, assessments, risks]) => setState({ runtime, systems, assessments, risks }))
      .catch((error: Error) => setState((current) => ({ ...current, error: error.message })));
  }, []);

  const summary = useMemo(() => {
    const highRisk = state.assessments.filter((item) => riskOrder[item.risk_classification.risk_level] >= 3);
    const pending = state.assessments.filter((item) => item.human_review_status !== "approved");
    const missingEvidence = state.assessments.flatMap((item) => item.evidence_checklist).filter((item) => item.status === "missing");
    const openRisks = state.risks.filter((item) => item.status !== "closed");
    return { highRisk, pending, missingEvidence, openRisks };
  }, [state.assessments, state.risks]);

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
        </nav>
        <div className="runtime">
          <span>Tenant</span>
          <strong>{state.runtime?.default_tenant_id || "default"}</strong>
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
            <h1>Governance command center</h1>
          </div>
          <div className="status">
            <CheckCircle2 size={18} />
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
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

export default App;
