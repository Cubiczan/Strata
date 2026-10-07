# Proposal

## Why

The owner is removing Anthropic Claude from every repo and moving LLM spend onto Amazon Nova, which AWS promotional credits cover. Strata still has an optional `anthropic` backend (Claude Haiku for grading, Claude Opus for authoring) that must be replaced so a leftover `STRATA_LLM_BACKEND=anthropic` setting cannot call Claude.

## What Changes

- **BREAKING**: Remove the Anthropic Claude backend (`anthropic` SDK, `ANTHROPIC_API_KEY`, Claude model defaults). `STRATA_LLM_BACKEND=anthropic` fails with a clear message that points operators at `bedrock`.
- Add a `bedrock` backend that calls Amazon Bedrock Runtime `Converse` through boto3, using the standard AWS credential chain and region `us-east-1` by default.
- Role models: Amazon Nova Pro `us.amazon.nova-pro-v1:0` for the author, Amazon Nova Lite `us.amazon.nova-lite-v1:0` for the grader. `STRATA_AUTHOR_MODEL` and `STRATA_GRADER_MODEL` still override those defaults.
- Keep DashScope / OpenAI-compatible (`STRATA_LLM_BACKEND=openai`) as the default backend.
- Drop the unused `anthropic` dependency from the `llm` extra and add `boto3`.
- Update `.env.example`, README, CLI help, the Streamlit status copy, and tests so no Anthropic code path remains.

## Capabilities

### New Capabilities

- `llm-backend`: Selects the live author and grader (DashScope by default, Amazon Nova on Bedrock when requested) and rejects the removed Anthropic backend.

### Modified Capabilities

- None. This repo has no existing specs.

## Impact

- Config and wiring: `src/strata/config.py`, `src/strata/orchestrator/director.py`, `src/strata/deliverable/author.py`, `src/strata/deliverable/grader.py`.
- Dependency: `pyproject.toml` `[project.optional-dependencies].llm`.
- Operator docs: `.env.example`, `README.md`, `src/strata/cli.py`, `streamlit_app.py`, `tests/test_live_llm.py`.
- Offline mock author/grader and the default DashScope path stay in place. Live Bedrock calls need AWS credentials; the default test suite stays offline.
