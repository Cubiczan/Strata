"""Amazon Bedrock Runtime Converse helper for Amazon Nova.

The client is built with boto3's standard credential chain (environment,
shared config, web identity, or instance role). No access keys are passed
in. The default region is us-east-1 so the US Nova inference profiles resolve.
"""

from __future__ import annotations

from typing import Any

from strata.config import get_settings

AUTHOR_SYSTEM = "You write CFO-grade financial deliverables. Be terse and tie out."


def bedrock_runtime_client(region: str | None = None) -> Any:
    """Return a bedrock-runtime client. Lazy-imports boto3."""
    try:
        import boto3
    except ImportError as e:
        raise ImportError(
            "install with `pip install -e '.[llm]'` to use the Amazon Bedrock backend"
        ) from e
    resolved = region or get_settings().aws_region
    return boto3.client("bedrock-runtime", region_name=resolved)


def converse_text(
    client: Any,
    *,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
) -> str:
    """Call Converse and concatenate text blocks from the assistant message."""
    resp = client.converse(
        modelId=model,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
    )
    content = resp["output"]["message"]["content"]
    parts: list[str] = []
    for block in content:
        text = block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts)
