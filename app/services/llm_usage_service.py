from collections.abc import Iterable
from typing import Any

from app.schemas.assessment import GovernanceAssessment
from app.schemas.llm_usage import LLMUsageSummary


LLM_TOOL_NAMES = {"llm_refiner"}


def summarize_llm_usage(
    assessments: Iterable[GovernanceAssessment],
    *,
    prompt_cost_per_1k_tokens: float = 0.0,
    completion_cost_per_1k_tokens: float = 0.0,
    assessment_id: str | None = None,
) -> LLMUsageSummary:
    assessment_list = list(assessments)
    tool_calls = [call for assessment in assessment_list for call in assessment.tool_calls]
    llm_calls = [call for call in tool_calls if _is_llm_call(call)]
    prompt_tokens = sum(_int(call.get("prompt_tokens")) for call in llm_calls)
    completion_tokens = sum(_int(call.get("completion_tokens")) for call in llm_calls)
    total_tokens = sum(_int(call.get("total_tokens")) for call in llm_calls) or prompt_tokens + completion_tokens
    total_latency_ms = round(sum(_float(call.get("latency_ms")) for call in llm_calls), 3)
    average_latency_ms = round(total_latency_ms / len(llm_calls), 3) if llm_calls else 0.0
    estimated_cost = None
    if prompt_cost_per_1k_tokens or completion_cost_per_1k_tokens:
        estimated_cost = round(
            (prompt_tokens / 1000 * prompt_cost_per_1k_tokens)
            + (completion_tokens / 1000 * completion_cost_per_1k_tokens),
            6,
        )

    return LLMUsageSummary(
        assessment_id=assessment_id,
        assessment_count=len(assessment_list),
        total_tool_calls=len(tool_calls),
        llm_call_count=len(llm_calls),
        successful_llm_call_count=sum(1 for call in llm_calls if call.get("status") == "success"),
        failed_llm_call_count=sum(1 for call in llm_calls if call.get("status") == "failed"),
        skipped_llm_call_count=sum(1 for call in llm_calls if call.get("status") == "skipped"),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        total_latency_ms=total_latency_ms,
        average_latency_ms=average_latency_ms,
        estimated_cost_usd=estimated_cost,
        providers=sorted({str(call["provider"]) for call in llm_calls if call.get("provider")}),
        models=sorted({str(call["model"]) for call in llm_calls if call.get("model")}),
        prompt_versions=sorted({str(call["prompt_version"]) for call in llm_calls if call.get("prompt_version")}),
    )


def _is_llm_call(call: dict[str, Any]) -> bool:
    if call.get("tool_name") in LLM_TOOL_NAMES:
        return True
    return any(key in call for key in ["provider", "model", "prompt_tokens", "completion_tokens", "total_tokens"])


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
