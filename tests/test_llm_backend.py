"""Offline coverage for the DashScope default and the Amazon Nova Bedrock backend."""

from __future__ import annotations

import builtins
import sys
from types import ModuleType

import pytest

from strata import config
from strata.config import (
    BEDROCK_AUTHOR_MODEL,
    BEDROCK_GRADER_MODEL,
    DEFAULT_BEDROCK_REGION,
    REMOVED_ANTHROPIC_BACKEND,
    get_settings,
)
from strata.deliverable.bedrock import converse_text


def _clear_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "STRATA_LLM_BACKEND",
        "STRATA_GRADER_MODEL",
        "STRATA_AUTHOR_MODEL",
        "STRATA_LLM_BASE_URL",
        "DASHSCOPE_API_KEY",
        "OPENAI_API_KEY",
        "STRATA_LLM_API_KEY",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "ANTHROPIC_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()


def test_default_backend_is_dashscope(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    settings = get_settings()
    assert settings.llm_backend == "openai"
    assert settings.grader_model == "qwen3.6-flash"
    assert settings.author_model == "qwen3.6-flash"
    assert settings.llm_base_url == config._DEFAULT_DASHSCOPE_BASE_URL
    get_settings.cache_clear()


def test_bedrock_defaults_to_nova(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "bedrock")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.llm_backend == "bedrock"
    assert settings.author_model == BEDROCK_AUTHOR_MODEL
    assert settings.grader_model == BEDROCK_GRADER_MODEL
    assert settings.aws_region == DEFAULT_BEDROCK_REGION
    assert settings.llm_api_key is None
    assert settings.llm_base_url is None
    get_settings.cache_clear()


def test_bedrock_model_and_region_overrides(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "bedrock")
    monkeypatch.setenv("STRATA_AUTHOR_MODEL", "custom-author")
    monkeypatch.setenv("STRATA_GRADER_MODEL", "custom-grader")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.author_model == "custom-author"
    assert settings.grader_model == "custom-grader"
    assert settings.aws_region == "us-west-2"
    get_settings.cache_clear()


def test_aws_default_region_used_when_aws_region_unset(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "bedrock")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-2")
    get_settings.cache_clear()
    assert get_settings().aws_region == "us-east-2"
    get_settings.cache_clear()


def test_anthropic_backend_is_rejected(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "anthropic")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="STRATA_LLM_BACKEND=bedrock") as exc:
        get_settings()
    assert "anthropic" in str(exc.value)
    assert str(exc.value) == REMOVED_ANTHROPIC_BACKEND
    get_settings.cache_clear()


def test_converse_text_joins_blocks():
    class FakeClient:
        def converse(self, **kwargs):
            self.kwargs = kwargs
            return {
                "output": {
                    "message": {
                        "content": [
                            {"text": "hello "},
                            {"text": ""},
                            {"image": "ignored"},
                            {"text": "world"},
                        ]
                    }
                }
            }

    client = FakeClient()
    text = converse_text(client, model="m", system="sys", user="prompt", max_tokens=128)
    assert text == "hello world"
    assert client.kwargs == {
        "modelId": "m",
        "system": [{"text": "sys"}],
        "messages": [{"role": "user", "content": [{"text": "prompt"}]}],
        "inferenceConfig": {"maxTokens": 128, "temperature": 0},
    }


def test_bedrock_client_uses_credential_chain(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "bedrock")
    get_settings.cache_clear()
    captured: dict = {}

    def client(service_name, **kwargs):
        captured["service"] = service_name
        captured["kwargs"] = kwargs
        return object()

    fake = ModuleType("boto3")
    fake.client = client  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "boto3", fake)

    from strata.deliverable.bedrock import bedrock_runtime_client

    bedrock_runtime_client()
    assert captured["service"] == "bedrock-runtime"
    assert captured["kwargs"] == {"region_name": DEFAULT_BEDROCK_REGION}
    assert "aws_access_key_id" not in captured["kwargs"]
    get_settings.cache_clear()


def test_missing_boto3_raises_install_hint(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delitem(sys.modules, "boto3", raising=False)
    real_import = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "boto3":
            raise ImportError("simulated")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded)
    from strata.deliverable.bedrock import bedrock_runtime_client

    with pytest.raises(ImportError, match=r"pip install -e '.\[llm\]'"):
        bedrock_runtime_client()


def test_bedrock_grader_and_author_call_converse(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "bedrock")
    get_settings.cache_clear()

    calls: list[dict] = []

    class FakeClient:
        def converse(self, **kwargs):
            calls.append(kwargs)
            return {"output": {"message": {"content": [{"text": "draft"}]}}}

    monkeypatch.setattr(
        "strata.deliverable.bedrock.bedrock_runtime_client",
        lambda region=None: FakeClient(),
    )

    from strata import registry
    from strata.deliverable.author import bedrock_author_factory
    from strata.deliverable.grader import BedrockLLM
    from strata.deliverable.persona import get_persona

    grader = BedrockLLM()
    assert grader.complete("grade this", "the draft") == "draft"
    assert calls[0]["modelId"] == BEDROCK_GRADER_MODEL
    assert calls[0]["inferenceConfig"]["maxTokens"] == 2048

    author = bedrock_author_factory()
    rubric = registry.get("rb.deliverable.board_pack")
    assert author(get_persona(rubric.rubric_id), rubric, {"company": "Acme"}, []) == "draft"
    assert calls[1]["modelId"] == BEDROCK_AUTHOR_MODEL
    assert calls[1]["inferenceConfig"]["maxTokens"] == 4096
    assert calls[1]["system"][0]["text"].startswith("You write CFO-grade")
    get_settings.cache_clear()


def test_director_selects_bedrock_backend(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "bedrock")
    get_settings.cache_clear()

    def sentinel_author(*_a, **_k):
        return "draft"

    class SentinelLLM:
        def complete(self, system: str, user: str) -> str:
            return "{}"

    llm = SentinelLLM()
    monkeypatch.setattr(
        "strata.deliverable.author.bedrock_author_factory",
        lambda model=None: sentinel_author,
    )
    monkeypatch.setattr("strata.deliverable.grader.BedrockLLM", lambda *a, **k: llm)

    from strata import registry
    from strata.orchestrator.chains import all_chains
    from strata.orchestrator.director import Director

    chain = all_chains()[0]
    factory = Director(persist=False, use_llm=True)._build_factory(
        chain, registry.get(chain.rubric_id)
    )
    assert factory.author is sentinel_author
    assert factory.grader._llm is llm
    get_settings.cache_clear()


def test_director_selects_openai_backend(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "openai")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    get_settings.cache_clear()

    def sentinel_author(*_a, **_k):
        return "draft"

    class SentinelLLM:
        def complete(self, system: str, user: str) -> str:
            return "{}"

    llm = SentinelLLM()
    monkeypatch.setattr(
        "strata.deliverable.author.openai_compatible_author_factory",
        lambda model=None: sentinel_author,
    )
    monkeypatch.setattr(
        "strata.deliverable.grader.OpenAICompatibleLLM",
        lambda *a, **k: llm,
    )

    from strata import registry
    from strata.orchestrator.chains import all_chains
    from strata.orchestrator.director import Director

    chain = all_chains()[0]
    factory = Director(persist=False, use_llm=True)._build_factory(
        chain, registry.get(chain.rubric_id)
    )
    assert factory.author is sentinel_author
    assert factory.grader._llm is llm
    get_settings.cache_clear()


def test_director_rejects_unknown_backend(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "other")
    get_settings.cache_clear()

    from strata import registry
    from strata.orchestrator.chains import all_chains
    from strata.orchestrator.director import Director

    chain = all_chains()[0]
    with pytest.raises(ValueError, match="expected 'openai' or 'bedrock'"):
        Director(persist=False, use_llm=True)._build_factory(chain, registry.get(chain.rubric_id))
    get_settings.cache_clear()


def test_director_rejects_anthropic_before_any_client(monkeypatch: pytest.MonkeyPatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("STRATA_LLM_BACKEND", "Anthropic")
    get_settings.cache_clear()

    from strata import registry
    from strata.orchestrator.chains import all_chains
    from strata.orchestrator.director import Director

    chain = all_chains()[0]
    with pytest.raises(ValueError, match="bedrock"):
        Director(persist=False, use_llm=True)._build_factory(chain, registry.get(chain.rubric_id))
    get_settings.cache_clear()
