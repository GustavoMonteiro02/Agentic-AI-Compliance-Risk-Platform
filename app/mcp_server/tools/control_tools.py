from app.agents.nodes.control_mapper import CONTROL_LIBRARY


def map_requirement_to_control(requirement: dict) -> dict:
    requirement_id = requirement.get("requirement_id", "")
    key = next((name for name in CONTROL_LIBRARY if name in requirement_id), "HUMAN_OVERSIGHT")
    control = CONTROL_LIBRARY[key]
    return {
        "requirement": requirement.get("title", requirement_id),
        "mapped_control": control["control"],
        "evidence_needed": control["evidence"],
        "control_status": "unknown",
    }


def create_compliance_task(title: str, owner: str, priority: str = "medium") -> dict:
    return {"title": title, "owner": owner, "priority": priority, "status": "open"}

