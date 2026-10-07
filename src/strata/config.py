from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Default LLM backend = OpenAI-compatible pointing at DashScope International.
# Set STRATA_LLM_BACKEND=bedrock to use Amazon Nova on Amazon Bedrock.
_DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
BEDROCK_AUTHOR_MODEL = "us.amazon.nova-pro-v1:0"
BEDROCK_GRADER_MODEL = "us.amazon.nova-lite-v1:0"
DEFAULT_BEDROCK_REGION = "us-east-1"
REMOVED_ANTHROPIC_BACKEND = (
    "STRATA_LLM_BACKEND=anthropic is no longer supported. Claude has been removed. "
    "Set STRATA_LLM_BACKEND=bedrock to use Amazon Nova on Amazon Bedrock "
    f"(author: {BEDROCK_AUTHOR_MODEL}, grader: {BEDROCK_GRADER_MODEL})."
)


@dataclass(frozen=True)
class Settings:
    database_url: str
    llm_backend: str  # "openai" (DashScope-compatible) | "bedrock"
    llm_api_key: str | None  # active backend key (None for Bedrock credential chain)
    llm_base_url: str | None  # active backend base URL (None = SDK default / Bedrock)
    grader_model: str
    author_model: str
    aws_region: str  # Bedrock region; default us-east-1
    max_iterations: int
    pass_threshold: float
    project_root: Path
    # Astra DB (vector exemplar store) — additive; Postgres stays relational core
    astra_api_endpoint: str | None
    astra_token: str | None
    astra_keyspace: str
    exemplar_top_k: int

    @property
    def has_llm_key(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def has_astra(self) -> bool:
        return bool(self.astra_api_endpoint and self.astra_token)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    test_db = os.getenv("STRATA_TEST_DB")
    db = test_db or os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://strata:strata@localhost:5433/strata",
    )
    backend = os.getenv("STRATA_LLM_BACKEND", "openai").lower()
    if backend == "anthropic":
        raise ValueError(REMOVED_ANTHROPIC_BACKEND)

    aws_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or DEFAULT_BEDROCK_REGION

    if backend == "bedrock":
        # boto3 default credential chain; no application API key.
        llm_api_key = None
        llm_base_url = None
        grader_default = BEDROCK_GRADER_MODEL
        author_default = BEDROCK_AUTHOR_MODEL
    else:
        # openai-compatible (DashScope by default)
        llm_api_key = (
            os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("STRATA_LLM_API_KEY")
        )
        llm_base_url = os.getenv("STRATA_LLM_BASE_URL", _DEFAULT_DASHSCOPE_BASE_URL)
        grader_default = "qwen3.6-flash"
        author_default = "qwen3.6-flash"

    return Settings(
        database_url=db,
        llm_backend=backend,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        grader_model=os.getenv("STRATA_GRADER_MODEL", grader_default),
        author_model=os.getenv("STRATA_AUTHOR_MODEL", author_default),
        aws_region=aws_region,
        max_iterations=int(os.getenv("STRATA_MAX_ITERATIONS", "5")),
        pass_threshold=float(os.getenv("STRATA_PASS_THRESHOLD", "8")),
        project_root=PROJECT_ROOT,
        astra_api_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT") or None,
        astra_token=os.getenv("ASTRA_DB_APPLICATION_TOKEN") or None,
        astra_keyspace=os.getenv("ASTRA_DB_KEYSPACE", "default_keyspace"),
        exemplar_top_k=int(os.getenv("STRATA_EXEMPLAR_TOP_K", "3")),
    )
