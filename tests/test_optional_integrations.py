from app.llm.provider import OptionalLLMProvider
from app.observability.langsmith import langsmith_trace_metadata
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
    assert metadata["total_tokens"] == 14
    assert metadata["latency_ms"] >= 0


def test_langsmith_trace_metadata_is_disabled_by_default():
    metadata = langsmith_trace_metadata("assessment-1", "workflow")

    assert metadata == {"enabled": False}


def test_simple_pdf_renderer_returns_pdf_bytes():
    pdf = markdown_to_simple_pdf("# Title\n\nBody", "Title")

    assert pdf.startswith(b"%PDF")
    assert b"%%EOF" in pdf
