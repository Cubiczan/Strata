# Tasks

## 1. Settings and dependency

- [x] 1.1 Reject `STRATA_LLM_BACKEND=anthropic` in `get_settings` with an error that names `bedrock`, add Bedrock Nova defaults and `aws_region`, remove `anthropic_api_key`, and verify unit tests for default DashScope, Nova defaults, model and region overrides, and the anthropic error
- [x] 1.2 Replace the `anthropic` extra dependency with `boto3` in `pyproject.toml` and update the `live_llm` marker text, then verify `anthropic` is absent from `pyproject.toml`

## 2. Bedrock Converse clients

- [x] 2.1 Add a shared Bedrock Runtime Converse helper (standard credential chain, no explicit keys) and wire `BedrockLLM` plus `bedrock_author_factory`, deleting the Anthropic classes, then verify offline tests of the Converse payload, region, missing-boto3 error, and text extraction
- [x] 2.2 Select the Bedrock author and grader from `Director._build_factory` when the backend is `bedrock`, reject other values with `openai` or `bedrock` in the message, and verify a director unit test for both paths

## 3. Operator-facing copy

- [x] 3.1 Update `.env.example`, README, CLI `--use-llm` help, Streamlit backend status, observability comment, and `tests/test_live_llm.py` so they describe DashScope and Bedrock and contain no Anthropic usage, then verify a repo search for `anthropic` and `claude` only hits the rejection message and historical migration notes

## 4. Integration check

- [x] 4.1 Run `ruff check src tests` and `pytest --cov` and verify both pass with no remaining Anthropic code path
