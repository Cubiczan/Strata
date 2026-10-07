# llm-backend Specification

## Purpose
Selects the live author and rubric grader, defaulting to DashScope and offering Amazon Nova on Amazon Bedrock, while refusing the removed Anthropic Claude backend.

## Requirements

### Requirement: DashScope remains the default backend
When `STRATA_LLM_BACKEND` is unset or `openai`, the system SHALL use the OpenAI-compatible DashScope backend. The default grader model SHALL be `qwen3.6-flash` and the default author model SHALL be `qwen3.6-flash`.

#### Scenario: Unset backend
- **WHEN** `STRATA_LLM_BACKEND` is unset and live LLM mode is requested
- **THEN** the author and grader use the OpenAI-compatible client against the configured DashScope base URL with model `qwen3.6-flash`

#### Scenario: Explicit openai backend
- **WHEN** `STRATA_LLM_BACKEND=openai` and live LLM mode is requested
- **THEN** the author and grader use the OpenAI-compatible client, not Amazon Bedrock

### Requirement: Bedrock backend uses Amazon Nova
When `STRATA_LLM_BACKEND=bedrock`, the system SHALL call Amazon Bedrock Runtime Converse. The author role SHALL use `us.amazon.nova-pro-v1:0` unless `STRATA_AUTHOR_MODEL` is set. The grader role SHALL use `us.amazon.nova-lite-v1:0` unless `STRATA_GRADER_MODEL` is set.

#### Scenario: Default Nova models
- **WHEN** `STRATA_LLM_BACKEND=bedrock` and neither model override is set
- **THEN** the author model is `us.amazon.nova-pro-v1:0` and the grader model is `us.amazon.nova-lite-v1:0`

#### Scenario: Model overrides
- **WHEN** `STRATA_LLM_BACKEND=bedrock` and `STRATA_AUTHOR_MODEL` and `STRATA_GRADER_MODEL` are set
- **THEN** those values replace the Nova Pro and Nova Lite defaults for the matching role

### Requirement: Bedrock uses the AWS credential chain in us-east-1
The Bedrock client SHALL be created with boto3's standard credential chain and SHALL NOT require an application API key. The region SHALL be `us-east-1` unless `AWS_REGION` or `AWS_DEFAULT_REGION` is set.

#### Scenario: Default region
- **WHEN** `STRATA_LLM_BACKEND=bedrock` and no AWS region variable is set
- **THEN** Converse requests are sent to `us-east-1`

#### Scenario: Region override
- **WHEN** `STRATA_LLM_BACKEND=bedrock` and `AWS_REGION` is set
- **THEN** Converse requests use that region

#### Scenario: No API key
- **WHEN** `STRATA_LLM_BACKEND=bedrock` and no DashScope or OpenAI API key is set
- **THEN** the Bedrock client is still constructed from the AWS credential chain

### Requirement: Removed Anthropic backend fails closed
`STRATA_LLM_BACKEND=anthropic` SHALL fail before any model call. The error SHALL name `bedrock` as the replacement. The system SHALL NOT import or call the Anthropic SDK.

#### Scenario: Legacy backend value
- **WHEN** `STRATA_LLM_BACKEND=anthropic`
- **THEN** configuration loading raises an error that tells the operator to use `STRATA_LLM_BACKEND=bedrock`

#### Scenario: No Claude dependency
- **WHEN** the package optional LLM extra is installed
- **THEN** it includes `boto3` and does not include the `anthropic` package

### Requirement: Unknown backends are rejected
A `STRATA_LLM_BACKEND` value other than `openai` or `bedrock` SHALL be rejected when live LLM mode is requested, and the error SHALL name the accepted values.

#### Scenario: Unrecognized backend
- **WHEN** live LLM mode is requested with `STRATA_LLM_BACKEND` set to a value other than `openai` or `bedrock`
- **THEN** the run fails with an error that expects `openai` or `bedrock`

### Requirement: Offline mode ignores the live backend
When live LLM mode is off, the system SHALL keep using the deterministic mock author and grader regardless of `STRATA_LLM_BACKEND`.

#### Scenario: Mock run
- **WHEN** a chain runs without live LLM mode and `STRATA_LLM_BACKEND` is unset
- **THEN** the mock author and grader produce the draft and scores
