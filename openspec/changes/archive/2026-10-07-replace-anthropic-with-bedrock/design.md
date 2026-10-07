# Design

## Context

See proposal.md for motivation. Today `get_settings()` branches on `STRATA_LLM_BACKEND=anthropic` and otherwise treats every value as OpenAI-compatible DashScope. `Director._build_factory` then instantiates `AnthropicLLM` plus `anthropic_author_factory`, or `OpenAICompatibleLLM` plus `openai_compatible_author_factory`. The Anthropic classes lazy-import the `anthropic` SDK. The offline suite never calls them (`pragma: no cover`).

## Goals / Non-Goals

**Goals:**

- One Bedrock Converse implementation shared by the grader and the author.
- Fail closed on `anthropic` at settings load so it cannot fall through into the DashScope branch.
- Keep the default backend and default Qwen model ids unchanged.
- Cover the new selection and Converse payload with offline tests that do not install boto3 or call AWS.

**Non-Goals:**

- Switching the default backend to Bedrock.
- Adding a new API key env var for Bedrock.
- Changing rubric scoring, prompts, iteration limits, or the mock path.
- Instrumenting Bedrock spans in Datadog beyond the existing no-op bootstrap.

## Decisions

1. **Reject `anthropic` inside `get_settings()`.** The current `else` branch is "anything that is not anthropic is DashScope." Removing the branch without an explicit error would silently send Claude-configured environments to Qwen. Raising `ValueError` at load time also fails CLI, API, and Streamlit runs that still have the old value, which is the desired migration signal. The message names `STRATA_LLM_BACKEND=bedrock`.

2. **Bedrock client via `boto3.client("bedrock-runtime", region_name=...)` with no credential arguments.** Omitting access keys keeps the standard chain (env, shared config, web identity, instance role). Region defaults to `us-east-1` because the `us.amazon.nova-*` ids are US cross-region inference profiles. `AWS_REGION` then `AWS_DEFAULT_REGION` override that default.

3. **Shared `converse` helper.** Both roles call `client.converse` with `system=[{"text": ...}]`, a single user message, and `inferenceConfig` of `temperature=0` plus `maxTokens` 2048 (grader) or 4096 (author). Those token caps match the existing backends and sit under Nova's output limit. Text blocks in the response are concatenated.

4. **Model defaults live on the settings object**, same as today: grader `us.amazon.nova-lite-v1:0`, author `us.amazon.nova-pro-v1:0`, overridable by `STRATA_GRADER_MODEL` and `STRATA_AUTHOR_MODEL`. Remove `Settings.anthropic_api_key`; nothing else reads it.

5. **`boto3` replaces `anthropic` in the `llm` extra.** The SDK stays optional. Constructors lazy-import it and raise `ImportError` with the existing `pip install -e '.[llm]'` hint. Tests inject a fake client or a fake `boto3` module so CI (`pip install -e ".[dev]"`) stays offline.

6. **Unknown backend values stay valid in `get_settings()` and fail in the director** when live mode is on, with the accepted set updated to `openai` or `bedrock`. Only `anthropic` is special-cased earlier so the error can point at the replacement.

## Risks / Trade-offs

- [A leftover `STRATA_LLM_BACKEND=anthropic` breaks every `get_settings()` caller, including mock runs and DB setup] → The error is immediate and names the fix. Leaving it to fall through would hide the misconfiguration.
- [Nova output capped at 4096 tokens can truncate a long deliverable] → Same cap the Claude and DashScope authors already use.
- [Live Bedrock tests need real AWS credentials and are easy to skip forever] → The opt-in `live_llm` marker treats an explicit `bedrock` backend as opted in; the default suite does not call AWS.
- [boto3 is a large optional dependency] → It is not imported unless the Bedrock backend is constructed.

## Migration Plan

1. Set `STRATA_LLM_BACKEND=bedrock` (or leave the default `openai`).
2. Provide AWS credentials through the standard chain and, if needed, `AWS_REGION=us-east-1`.
3. Remove `ANTHROPIC_API_KEY` and any Claude model overrides.
4. Reinstall the `llm` extra so `boto3` is present and `anthropic` is not required.
5. Rollback is reverting this change; there is no data migration.

## Open Questions

None. Model ids, region, API, and the default backend were specified by the request.
