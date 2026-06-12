from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.llm.provider import OptionalLLMProvider


def main() -> int:
    provider = OptionalLLMProvider()
    if not provider.enabled():
        print(
            "LLM provider is not enabled. Copy .env.example to .env, set OPENAI_API_KEY, "
            "and ensure AI_GENERATION_MODE=llm."
        )
        return 1

    result = provider.structured_json_result(
        "You are a JSON-only smoke test for an AI governance platform.",
        'Return exactly one JSON object with keys "ok", "provider_check", and "message".',
    )
    if not result:
        print("LLM provider returned no result.")
        return 1

    payload, metadata = result
    print("LLM smoke test passed.")
    print(
        {
            "payload": payload,
            "provider": metadata.get("provider"),
            "model": metadata.get("model"),
            "attempts": metadata.get("attempts"),
            "total_tokens": metadata.get("total_tokens"),
            "latency_ms": metadata.get("latency_ms"),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
