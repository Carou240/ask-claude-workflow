import os
from datetime import timedelta

import httpx
from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import WorkflowsException

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-5"


class AskClaudeInput(BaseModel):
    question: str
    model: str = DEFAULT_MODEL
    max_tokens: int = 2048
    system: str | None = None


class AskClaudeOutput(BaseModel):
    answer: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


@workflows.activity(
    start_to_close_timeout=timedelta(minutes=2),
    retry_policy_max_attempts=3,
    retry_policy_backoff_coefficient=2.0,
)
async def ask_claude(params: AskClaudeInput) -> AskClaudeOutput:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise WorkflowsException(
            code="MISSING_API_KEY",
            status=500,
            detail="ANTHROPIC_API_KEY is not configured on the deployment.",
        )

    payload = {
        "model": params.model,
        "max_tokens": params.max_tokens,
        "messages": [{"role": "user", "content": params.question}],
    }
    if params.system:
        payload["system"] = params.system

    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(ANTHROPIC_API_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise WorkflowsException(
            code="ANTHROPIC_API_ERROR",
            status=502,
            detail=f"Anthropic API returned {response.status_code}: {response.text[:500]}",
        )

    data = response.json()
    answer = "".join(
        block.get("text", "")
        for block in data.get("content", [])
        if block.get("type") == "text"
    )
    usage = data.get("usage", {})

    return AskClaudeOutput(
        answer=answer,
        model=data.get("model", params.model),
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )


@workflows.workflow.define(
    name="ask-claude",
    workflow_display_name="Ask Claude",
    workflow_description="Send a question to Claude (Anthropic API) and return its answer.",
)
class AskClaudeWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: AskClaudeInput) -> AskClaudeOutput:
        return await ask_claude(input)
