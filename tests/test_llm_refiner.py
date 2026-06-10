from app.agents.nodes.llm_refiner import llm_refiner_node


def test_llm_refiner_applies_structured_output(monkeypatch):
    class FakeProvider:
        def enabled(self):
            return True

        def structured_json(self, _system_prompt, _user_prompt):
            return {
                "risk_classification": {
                    "risk_level": "high",
                    "confidence": 0.91,
                    "risk_factors": ["employment context", "personal data processing"],
                    "reasoning_summary": "LLM refined draft, pending human review.",
                    "requires_human_review": True,
                    "requires_additional_information": False,
                },
                "mapped_controls": [
                    {
                        "requirement_id": "HUMAN_OVERSIGHT_001",
                        "requirement": "Human oversight",
                        "mapped_control": "Document reviewer approval workflow.",
                        "evidence_needed": ["Human oversight SOP"],
                        "control_status": "missing",
                    }
                ],
                "gap_analysis": {
                    "overall_status": "not_ready_for_audit",
                    "critical_gaps": [
                        {
                            "gap": "Human oversight SOP missing",
                            "risk": "High",
                            "recommended_action": "Create human oversight SOP.",
                        }
                    ],
                    "medium_gaps": [],
                    "low_gaps": [],
                    "priority_actions": ["Create human oversight SOP."],
                },
                "evidence_checklist": [
                    {"evidence": "Human oversight SOP", "status": "missing", "priority": "high", "owner": "Compliance"}
                ],
                "ai_system_card_markdown": "# AI System Card\n\nDraft only.",
                "audit_report_markdown": "# Audit Report\n\nDraft only.",
            }

    monkeypatch.setattr("app.agents.nodes.llm_refiner.OptionalLLMProvider", FakeProvider)
    state = {
        "system_profile": {"system_name": "HR Assistant"},
        "risk_classification": {},
        "retrieved_requirements": [],
        "mapped_controls": [],
        "gap_analysis": {},
        "evidence_checklist": [],
        "ai_system_card": {"title": "Card", "content_markdown": "", "content_json": {}, "status": "draft"},
        "audit_report": {"title": "Report", "content_markdown": "", "content_json": {}, "status": "draft"},
        "tool_calls": [],
        "errors": [],
    }

    updated = llm_refiner_node(state)

    assert updated["risk_classification"]["confidence"] == 0.91
    assert updated["ai_system_card"]["content_markdown"].startswith("# AI System Card")
    assert updated["tool_calls"][-1]["status"] == "success"

