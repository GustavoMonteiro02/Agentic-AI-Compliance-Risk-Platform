from app.agents.nodes.audit_report_generator import audit_report_generator_node
from app.agents.nodes.system_card_generator import system_card_generator_node


def generate_ai_system_card(state: dict) -> dict:
    return system_card_generator_node({**state, "tool_calls": []})["ai_system_card"]


def generate_audit_report(state: dict) -> dict:
    return audit_report_generator_node({**state, "tool_calls": []})["audit_report"]

