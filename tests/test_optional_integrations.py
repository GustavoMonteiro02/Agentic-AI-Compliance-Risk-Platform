import requests

from app.llm.provider import OptionalLLMProvider
from app.observability.langsmith import (
    build_langsmith_experiment_payload,
    langsmith_trace_metadata,
    upload_langsmith_experiment,
)
from app.services.pdf_service import markdown_to_simple_pdf


def test_optional_llm_provider_is_disabled_by_default():
    assert OptionalLLMProvider().enabled() is False


def test_optional_llm_provider_parses_structured_metadata(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": '{"ok": true}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
            }

    provider = OptionalLLMProvider()
    monkeypatch.setattr(provider, "enabled", lambda: True)
    monkeypatch.setattr("app.llm.provider.requests.post", lambda *args, **kwargs: FakeResponse())

    result = provider.structured_json_result("system", "user")

    assert result is not None
    payload, metadata = result
    assert payload == {"ok": True}
    assert metadata["provider"] == "openai"
    assert metadata["attempts"] == 1
    assert metadata["total_tokens"] == 14
    assert metadata["latency_ms"] >= 0


def test_optional_llm_provider_parses_anthropic_structured_response(monkeypatch):
    class FakeResponse:
        content = b"{}"

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "content": [{"type": "text", "text": '{"ok": true}'}],
                "usage": {"input_tokens": 8, "output_tokens": 5},
            }

    provider = OptionalLLMProvider()
    monkeypatch.setattr(provider.settings, "ai_generation_mode", "llm")
    monkeypatch.setattr(provider.settings, "llm_provider", "anthropic")
    monkeypatch.setattr(provider.settings, "anthropic_api_key", "test")
    monkeypatch.setattr("app.llm.provider.requests.post", lambda *args, **kwargs: FakeResponse())

    result = provider.structured_json_result("system", "user")

    assert result is not None
    payload, metadata = result
    assert payload == {"ok": True}
    assert metadata["provider"] == "anthropic"
    assert metadata["model"] == provider.settings.anthropic_model
    assert metadata["prompt_tokens"] == 8
    assert metadata["completion_tokens"] == 5
    assert metadata["total_tokens"] == 13


def test_optional_llm_provider_retries_transient_failures(monkeypatch):
    calls = {"count": 0}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": '{"ok": true}'}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            }

    def flaky_post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.Timeout("temporary timeout")
        return FakeResponse()

    provider = OptionalLLMProvider()
    provider.settings.openai_max_retries = 1
    monkeypatch.setattr(provider, "enabled", lambda: True)
    monkeypatch.setattr("app.llm.provider.requests.post", flaky_post)

    result = provider.structured_json_result("system", "user")

    assert result is not None
    payload, metadata = result
    assert payload == {"ok": True}
    assert metadata["attempts"] == 2


def test_langsmith_trace_metadata_is_disabled_by_default():
    metadata = langsmith_trace_metadata("assessment-1", "workflow")

    assert metadata == {"enabled": False}


def test_langsmith_experiment_payload_is_upload_ready_without_credentials():
    payload = build_langsmith_experiment_payload(
        [{"metric_name": "retrieval_quality", "score": 1.0, "details": {"cases": 4}}],
        "local-test",
    )
    upload_result = upload_langsmith_experiment(payload)

    assert payload["experiment_name"] == "local-test"
    assert payload["summary"]["average_score"] == 1.0
    assert payload["runs"][0]["outputs"]["details"] == {"cases": 4}
    assert upload_result["uploaded"] is False
    assert upload_result["reason"] == "missing_langsmith_api_key"


def test_simple_pdf_renderer_returns_pdf_bytes():
    pdf = markdown_to_simple_pdf("# Title\n\nBody", "Title")

    assert pdf.startswith(b"%PDF")
    assert b"%%EOF" in pdf
