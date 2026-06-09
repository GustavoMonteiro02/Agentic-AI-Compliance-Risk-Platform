from app.agents.graph import WORKFLOW_NODE_NAMES, build_governance_graph, run_governance_assessment


def test_langgraph_workflow_compiles_and_runs():
    graph = build_governance_graph()
    assessment = run_governance_assessment(
        "system-langgraph",
        "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
    )

    assert graph is not None
    assert assessment.status == "needs_review"
    assert [call["tool_name"] for call in assessment.tool_calls]


def test_workflow_node_catalog_is_complete():
    assert WORKFLOW_NODE_NAMES == [
        "intake",
        "missing_info_checker",
        "risk_classifier",
        "regulatory_retriever",
        "control_mapper",
        "gap_analyzer",
        "evidence_generator",
        "system_card_generator",
        "audit_report_generator",
        "human_review",
    ]
