from pydantic import BaseModel, Field


class LLMUsageSummary(BaseModel):
    assessment_id: str | None = None
    assessment_count: int = 0
    total_tool_calls: int = 0
    llm_call_count: int = 0
    successful_llm_call_count: int = 0
    failed_llm_call_count: int = 0
    skipped_llm_call_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    average_latency_ms: float = 0.0
    estimated_cost_usd: float | None = None
    providers: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    prompt_versions: list[str] = Field(default_factory=list)
