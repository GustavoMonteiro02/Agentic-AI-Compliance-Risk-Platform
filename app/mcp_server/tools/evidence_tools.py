from app.agents.nodes.evidence_generator import evidence_generator_node


def generate_evidence_checklist(mapped_controls: list[dict]) -> list[dict]:
    state = {"mapped_controls": mapped_controls, "tool_calls": []}
    return evidence_generator_node(state)["evidence_checklist"]

