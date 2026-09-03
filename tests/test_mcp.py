"""Stdio MCP pipe: tools/list plus assessment/roadmap against sample fixtures."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp.client.client import Client
from mcp.client.stdio import StdioServerParameters, get_default_environment

from strata.mcp.serialize import verdict_for
from strata.mcp.server import create_server
from strata.mcp.tools import (
    assess_maturity,
    list_registered_chains,
    list_registered_rubrics,
    plan_90_day_roadmap,
    route_and_run_deliverable,
    run_deliverable_chain,
    server_version,
)

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
ASSESSMENT = SAMPLES / "maturity_self_assessment.yaml"
BOARD_PACK_INPUTS = SAMPLES / "board_pack_inputs.json"

EXPECTED_TOOLS = {
    "assess_maturity",
    "plan_90_day_roadmap",
    "list_chains",
    "run_chain",
    "route_chain",
    "list_rubrics",
    "strata_version",
}


def test_assess_maturity_wraps_sample_fixture():
    result = assess_maturity(self_assessment_path=str(ASSESSMENT), axis="both")
    assert result["target_id"] == "Acme Robotics"
    assert result["axis"] == "both"
    assert 30.0 <= result["function"]["overall_pct"] <= 65.0
    names = [row["name"] for row in result["function"]["heatmap"]]
    assert "Forecasting" in names
    assert {c["rubric_id"] for c in result["function"]["capabilities"]} >= {
        "rb.function.close",
        "rb.function.forecast",
    }
    assert "rb.competency.fpna" in {c["rubric_id"] for c in result["competency"]["capabilities"]}
    # heatmap stays weakest-first, same as MaturityAssessor.heatmap()
    pcts = [row["score_pct"] for row in result["function"]["heatmap"]]
    assert pcts == sorted(pcts)


def test_plan_90_day_roadmap_wraps_sample_fixture():
    result = plan_90_day_roadmap(self_assessment_path=str(ASSESSMENT), axis="function")
    assert result["target_id"] == "Acme Robotics"
    assert result["axis"] == "function"
    assert [p["label"] for p in result["phases"]] == ["Days 1-30", "Days 31-60", "Days 61-90"]
    assert result["phases"][0]["intent"] == "Baseline & Quick Wins"
    chain_ids = {
        action["chain_id"]
        for phase in result["phases"]
        for action in phase["actions"]
        if action["chain_id"]
    }
    assert chain_ids  # sample has weak capabilities that map to shipped chains
    assert all(
        cid.startswith("chain.") for cid in chain_ids
    ), "roadmap must point at in-repo chain ids, not invented ones"


def test_list_helpers_use_in_repo_ids_only():
    chains = list_registered_chains()
    rubrics = list_registered_rubrics()
    assert chains["count"] == 12
    assert "chain.board_pack.v1" in {c["chain_id"] for c in chains["chains"]}
    assert any(r["rubric_id"] == "rb.function.close" for r in rubrics["rubrics"])
    assert any(r["rubric_id"] == "rb.deliverable.board_pack" for r in rubrics["rubrics"])
    assert server_version()["brand"] == "Cubiczan"


def test_run_chain_scores_sample_board_pack():
    result = run_deliverable_chain(
        chain_id="chain.board_pack.v1",
        inputs_path=str(BOARD_PACK_INPUTS),
    )
    assert result["chain_id"] == "chain.board_pack.v1"
    assert result["rubric_id"] == "rb.deliverable.board_pack"
    assert result["iterations"] >= 1
    assert "Acme Robotics" in result["final_draft"]
    assert "normalized_pct" in result["final_score"]


def test_assess_inline_yaml_and_error_paths():
    yaml_text = ASSESSMENT.read_text(encoding="utf-8")
    result = assess_maturity(self_assessment_yaml=yaml_text, axis="function")
    assert result["axis"] == "function"
    assert result["overall_pct"] == result["function"]["overall_pct"]

    try:
        assess_maturity(self_assessment_path=str(ASSESSMENT), self_assessment_yaml=yaml_text)
    except ValueError as exc:
        assert "only one" in str(exc)
    else:
        raise AssertionError("expected exclusive-input error")

    try:
        assess_maturity(axis="both")
    except ValueError as exc:
        assert "provide self_assessment" in str(exc)
    else:
        raise AssertionError("expected missing-input error")

    try:
        assess_maturity(self_assessment_path="/no/such/assessment.yaml")
    except ValueError as exc:
        assert "not found" in str(exc)
    else:
        raise AssertionError("expected missing-file error")

    try:
        assess_maturity(self_assessment_yaml="- just a list\n", axis="function")
    except ValueError as exc:
        assert "YAML mapping" in str(exc)
    else:
        raise AssertionError("expected mapping error")

    try:
        assess_maturity(self_assessment_path=str(ASSESSMENT), axis="sideways")  # type: ignore[arg-type]
    except ValueError as exc:
        assert "axis" in str(exc)
    else:
        raise AssertionError("expected axis error")


def test_route_and_run_wraps_director():
    result = route_and_run_deliverable(
        self_assessment_path=str(ASSESSMENT),
        inputs_path=str(BOARD_PACK_INPUTS),
    )
    assert result["decision"]["chain_id"].startswith("chain.")
    assert result["run"]["chain_id"] == result["decision"]["chain_id"]
    assert result["run"]["iterations"] >= 1


def test_run_chain_input_errors():
    try:
        run_deliverable_chain(chain_id="chain.risk_register.v1")
    except ValueError as exc:
        assert "inputs" in str(exc)
    else:
        raise AssertionError("expected missing-inputs error")

    try:
        run_deliverable_chain(
            chain_id="chain.risk_register.v1",
            inputs={"company": "x"},
            inputs_path=str(BOARD_PACK_INPUTS),
        )
    except ValueError as exc:
        assert "only one" in str(exc)
    else:
        raise AssertionError("expected exclusive-inputs error")


def test_run_chain_accepts_inputs_dict():
    payload = json.loads(BOARD_PACK_INPUTS.read_text(encoding="utf-8"))
    result = run_deliverable_chain(chain_id="chain.risk_register.v1", inputs=payload)
    assert result["chain_id"] == "chain.risk_register.v1"
    assert result["rubric_id"] == "rb.deliverable.risk_register"


def test_verdict_and_lazy_export():
    import strata.mcp as mcp_pkg

    assert verdict_for(49) == "weak"
    assert verdict_for(50) == "developing"
    assert verdict_for(70) == "mature"
    assert mcp_pkg.create_server is create_server
    missing = "not_a_thing"
    try:
        getattr(mcp_pkg, missing)
    except AttributeError:
        pass
    else:
        raise AssertionError("expected AttributeError for unknown export")


def test_assess_errors_when_rubric_missing():
    yaml_text = "target_id: Incomplete\nrb.function.close:\n  team_understands_close_target: 3\n"
    try:
        assess_maturity(self_assessment_yaml=yaml_text, axis="function")
    except ValueError as exc:
        assert "missing scores" in str(exc)
        assert "rb.function.reconcile" in str(exc)
    else:
        raise AssertionError("expected missing-rubric ValueError")


def _text_payload(result) -> dict:
    if getattr(result, "structured_content", None):
        data = result.structured_content
        if isinstance(data, dict):
            return data
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            return json.loads(text)
    raise AssertionError(f"no JSON payload in tool result: {result!r}")


async def _inprocess_tools_list_and_roadmap() -> None:
    async with Client(create_server()) as client:
        listed = await client.list_tools()
        names = {t.name for t in listed.tools}
        assert names >= EXPECTED_TOOLS
        roadmap = _text_payload(
            await client.call_tool(
                "plan_90_day_roadmap",
                {
                    "self_assessment_path": str(ASSESSMENT),
                    "axis": "function",
                },
            )
        )
        assert roadmap["target_id"] == "Acme Robotics"
        assert [p["label"] for p in roadmap["phases"]] == [
            "Days 1-30",
            "Days 31-60",
            "Days 61-90",
        ]
        chains = _text_payload(await client.call_tool("list_chains", {}))
        assert chains["count"] == 12
        rubrics = _text_payload(await client.call_tool("list_rubrics", {}))
        assert any(r["rubric_id"] == "rb.function.close" for r in rubrics["rubrics"])
        version = _text_payload(await client.call_tool("strata_version", {}))
        assert version["brand"] == "Cubiczan"
        scored = _text_payload(
            await client.call_tool(
                "run_chain",
                {
                    "chain_id": "chain.risk_register.v1",
                    "inputs_path": str(SAMPLES / "risk_register_inputs.json"),
                },
            )
        )
        assert scored["chain_id"] == "chain.risk_register.v1"
        assert scored["rubric_id"] == "rb.deliverable.risk_register"


def test_inprocess_mcp_tools_list_and_roadmap():
    asyncio.run(_inprocess_tools_list_and_roadmap())


async def _stdio_tools_list_and_assess() -> None:
    env = get_default_environment()
    src = str(SAMPLES.parent / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src if not existing else f"{src}{os.pathsep}{existing}"

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "strata.mcp"],
        cwd=str(SAMPLES.parent),
        env=env,
    )
    async with Client(params) as client:
        listed = await client.list_tools()
        names = {t.name for t in listed.tools}
        assert names >= EXPECTED_TOOLS
        assessed = _text_payload(
            await client.call_tool(
                "assess_maturity",
                {
                    "self_assessment_path": str(ASSESSMENT),
                    "axis": "both",
                },
            )
        )
        assert assessed["target_id"] == "Acme Robotics"
        assert assessed["function"]["overall_pct"] > 0
        assert any(row["name"] == "Forecasting" for row in assessed["function"]["heatmap"])


def test_stdio_mcp_tools_list_and_assess():
    """Success criterion: stdio MCP starts; tools/list + assessment against samples/."""
    asyncio.run(_stdio_tools_list_and_assess())
