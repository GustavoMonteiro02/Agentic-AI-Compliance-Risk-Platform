from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_human_review_approval_requires_notes():
    system = client.post(
        "/systems",
        json={
            "name": "Review Guardrail System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess").json()

    response = client.post(
        f"/reviews/{assessment['id']}/approve",
        json={"reviewer": "Compliance Reviewer", "notes": ""},
    )

    assert response.status_code == 400


def test_human_review_can_approve_with_notes():
    system = client.post(
        "/systems",
        json={
            "name": "Approval Workflow System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess").json()

    response = client.post(
        f"/reviews/{assessment['id']}/approve",
        json={"reviewer": "Compliance Reviewer", "notes": "Approved after review of evidence plan."},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    audit_events = client.get(f"/audit/assessments/{assessment['id']}/events").json()
    assert audit_events[0]["action"] == "review.approved"
    assert audit_events[0]["actor"] == "local-dev"


def test_review_queue_and_history_are_available():
    system = client.post(
        "/systems",
        json={
            "name": "Queue Workflow System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess").json()

    queue_response = client.get("/reviews/queue")
    queue_ids = {item["assessment_id"] for item in queue_response.json()}
    assert assessment["id"] in queue_ids

    client.post(
        f"/reviews/{assessment['id']}/request-more-evidence",
        json={"reviewer": "Compliance Reviewer", "notes": "Need evaluation report."},
    )
    history = client.get(f"/reviews/{assessment['id']}/history").json()

    assert history[0]["status"] == "needs_more_evidence"
    assert history[0]["reviewer"] == "Compliance Reviewer"


def test_review_queue_surfaces_escalation_signals():
    system = client.post(
        "/systems",
        json={
            "name": "Escalation Workflow System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess").json()

    queue = client.get("/reviews/queue").json()
    escalations = client.get("/reviews/escalations").json()
    item = next(item for item in queue if item["assessment_id"] == assessment["id"])

    assert item["age_hours"] >= 0
    assert item["escalation_level"] in {"urgent", "attention", "sla_breach"}
    assert item["escalation_reason"]
    assert any(escalation["assessment_id"] == assessment["id"] for escalation in escalations)


def test_review_escalations_can_queue_notifications_without_duplicates():
    headers = {"X-Tenant-ID": "notify-tenant", "X-User-Role": "admin", "X-User": "review-ops"}
    system = client.post(
        "/systems",
        headers=headers,
        json={
            "name": "Notification Escalation System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess", headers=headers).json()

    first = client.post(
        "/reviews/escalations/notifications?recipient=compliance@example.com&channel=email",
        headers=headers,
    )
    second = client.post(
        "/reviews/escalations/notifications?recipient=compliance@example.com&channel=email",
        headers=headers,
    )
    listed = client.get(
        "/notifications?event_type=review_escalation",
        headers={"X-Tenant-ID": "notify-tenant", "X-User-Role": "auditor"},
    )
    tenant_b = client.get(
        "/notifications?event_type=review_escalation",
        headers={"X-Tenant-ID": "notify-tenant-b", "X-User-Role": "auditor"},
    )

    assert first.status_code == 200
    notifications = [item for item in first.json() if item["assessment_id"] == assessment["id"]]
    assert notifications
    notification = notifications[0]
    assert notification["event_type"] == "review_escalation"
    assert notification["status"] == "queued"
    assert notification["channel"] == "email"
    assert notification["recipient"] == "compliance@example.com"
    assert notification["payload_json"]["assessment_id"] == assessment["id"]
    assert second.status_code == 200
    assert [item["id"] for item in second.json() if item["assessment_id"] == assessment["id"]] == [notification["id"]]
    assert any(item["id"] == notification["id"] for item in listed.json())
    assert tenant_b.json() == []


def test_review_notification_events_are_included_in_audit_package():
    headers = {"X-Tenant-ID": "package-notify", "X-User-Role": "admin", "X-User": "review-ops"}
    system = client.post(
        "/systems",
        headers=headers,
        json={
            "name": "Notification Audit Package System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess", headers=headers).json()
    client.post("/reviews/escalations/notifications", headers=headers)

    package = client.get(
        f"/audit/assessments/{assessment['id']}/package",
        headers={"X-Tenant-ID": "package-notify", "X-User-Role": "auditor"},
    ).json()

    assert any(event["event_type"] == "review_escalation" for event in package["notification_events"])
    assert package["summary"]["notification_event_count"] >= 1


def test_notification_delivery_status_can_be_updated_and_audited():
    headers = {"X-Tenant-ID": "delivery-tenant", "X-User-Role": "admin", "X-User": "review-ops"}
    auditor_headers = {"X-Tenant-ID": "delivery-tenant", "X-User-Role": "auditor", "X-User": "audit-ops"}
    system = client.post(
        "/systems",
        headers=headers,
        json={
            "name": "Notification Delivery System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess", headers=headers).json()
    notification = client.post("/reviews/escalations/notifications", headers=headers).json()[0]

    delivered = client.patch(
        f"/notifications/{notification['id']}",
        headers=auditor_headers,
        json={"status": "delivered", "delivery_notes": "Accepted by downstream email gateway."},
    )
    tenant_b = client.patch(
        f"/notifications/{notification['id']}",
        headers={"X-Tenant-ID": "delivery-tenant-b", "X-User-Role": "auditor"},
        json={"status": "failed"},
    )
    events = client.get(f"/audit/assessments/{assessment['id']}/events", headers=auditor_headers).json()

    assert delivered.status_code == 200
    payload = delivered.json()
    assert payload["status"] == "delivered"
    assert payload["delivered_at"]
    assert payload["payload_json"]["delivery_notes"] == "Accepted by downstream email gateway."
    assert tenant_b.status_code == 404
    assert any(event["action"] == "notification.delivered" for event in events)
