from app.llm.provider import OptionalLLMProvider
from app.observability.langsmith import langsmith_trace_metadata
from app.services.pdf_service import markdown_to_simple_pdf


def test_optional_llm_provider_is_disabled_by_default():
    assert OptionalLLMProvider().enabled() is False


def test_langsmith_trace_metadata_is_disabled_by_default():
    metadata = langsmith_trace_metadata("assessment-1", "workflow")

    assert metadata == {"enabled": False}


def test_simple_pdf_renderer_returns_pdf_bytes():
    pdf = markdown_to_simple_pdf("# Title\n\nBody", "Title")

    assert pdf.startswith(b"%PDF")
    assert b"%%EOF" in pdf
