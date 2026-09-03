"""Pure wrappers around Strata entrypoints. No MCP protocol here.

Every function calls an existing assessor, roadmap, registry, or Director
method. Rubric IDs and chain IDs come from the repo — nothing is invented.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from strata import __version__, registry
from strata.maturity.load import (
    VALID_AXES,
    VALID_AXES_WITH_BOTH,
    load_assessment,
    load_self_assessment_file,
    parse_self_assessment_yaml,
)
from strata.maturity.roadmap import plan_90_days
from strata.mcp.serialize import (
    assessment_to_dict,
    chain_to_dict,
    director_run_to_dict,
    roadmap_to_dict,
    route_decision_to_dict,
    rubric_summary,
)
from strata.orchestrator.chains import all_chains
from strata.orchestrator.director import Director

Axis = Literal["function", "competency", "both"]


def _resolve_assessment_raw(
    self_assessment_path: str | None,
    self_assessment_yaml: str | None,
) -> tuple[dict[str, Any], str]:
    if self_assessment_path and self_assessment_yaml:
        raise ValueError("pass only one of self_assessment_path or self_assessment_yaml")
    if self_assessment_path:
        path = Path(self_assessment_path).expanduser()
        return load_self_assessment_file(path), str(path)
    if self_assessment_yaml:
        return parse_self_assessment_yaml(self_assessment_yaml), "<inline>"
    raise ValueError("provide self_assessment_path or self_assessment_yaml")


def assess_maturity(
    self_assessment_path: str | None = None,
    self_assessment_yaml: str | None = None,
    axis: Axis = "both",
) -> dict[str, Any]:
    """L1 dual-axis (or single-axis) maturity heatmap from a self-assessment."""
    if axis not in VALID_AXES_WITH_BOTH:
        raise ValueError(f"axis must be one of {VALID_AXES_WITH_BOTH}, got '{axis}'")
    raw, source = _resolve_assessment_raw(self_assessment_path, self_assessment_yaml)
    target_id = raw.get("target_id", "unnamed")
    payload: dict[str, Any] = {"target_id": target_id, "axis": axis, "source": source}
    axes = ("function", "competency") if axis == "both" else (axis,)
    for one in axes:
        payload[one] = assessment_to_dict(load_assessment(raw, axis=one, source=source))
    if axis != "both":
        payload["overall_pct"] = payload[axis]["overall_pct"]
    return payload


def plan_90_day_roadmap(
    self_assessment_path: str | None = None,
    self_assessment_yaml: str | None = None,
    axis: Literal["function", "competency"] = "function",
) -> dict[str, Any]:
    """90-day phased plan from ``plan_90_days`` (Director adapter)."""
    if axis not in VALID_AXES:
        raise ValueError(f"axis must be one of {VALID_AXES}, got '{axis}'")
    raw, source = _resolve_assessment_raw(self_assessment_path, self_assessment_yaml)
    assessment = load_assessment(raw, axis=axis, source=source)
    return roadmap_to_dict(plan_90_days(assessment, axis=axis))


def list_registered_chains() -> dict[str, Any]:
    """Fetch the chain registry. IDs and rubrics are those shipped in-repo."""
    chains = [chain_to_dict(c) for c in all_chains()]
    return {"count": len(chains), "chains": chains}


def list_registered_rubrics() -> dict[str, Any]:
    """Fetch loaded rubrics from ``src/strata/rubrics`` — no invented items."""
    loaded = sorted(registry.load_all().values(), key=lambda r: r.rubric_id)
    rubrics = [rubric_summary(rb) for rb in loaded]
    return {"count": len(rubrics), "rubrics": rubrics}


def _load_inputs(inputs: dict[str, Any] | None, inputs_path: str | None) -> dict[str, Any]:
    if inputs is not None and inputs_path:
        raise ValueError("pass only one of inputs or inputs_path")
    if inputs_path:
        path = Path(inputs_path).expanduser()
        if not path.is_file():
            raise ValueError(f"inputs file not found: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("inputs JSON must be an object")
        return payload
    if inputs is None:
        raise ValueError("provide inputs or inputs_path")
    return inputs


def run_deliverable_chain(
    chain_id: str,
    inputs: dict[str, Any] | None = None,
    inputs_path: str | None = None,
    use_llm: bool = False,
    persist: bool = False,
) -> dict[str, Any]:
    """Score a registered chain via ``Director.run_chain`` (mock author by default)."""
    payload = _load_inputs(inputs, inputs_path)
    director = Director(persist=persist, use_llm=use_llm)
    run = director.run_chain(chain_id, payload)
    return director_run_to_dict(run)


def route_and_run_deliverable(
    self_assessment_path: str | None = None,
    self_assessment_yaml: str | None = None,
    inputs: dict[str, Any] | None = None,
    inputs_path: str | None = None,
    axis: Literal["function", "competency"] = "function",
    use_llm: bool = False,
    persist: bool = False,
) -> dict[str, Any]:
    """``Director.route``: weakest-capability chain wins, then score it."""
    if axis not in VALID_AXES:
        raise ValueError(f"axis must be one of {VALID_AXES}, got '{axis}'")
    raw, source = _resolve_assessment_raw(self_assessment_path, self_assessment_yaml)
    assessment = load_assessment(raw, axis=axis, source=source)
    payload = _load_inputs(inputs, inputs_path)
    director = Director(persist=persist, use_llm=use_llm)
    decision, run = director.route(assessment, payload)
    return {
        "decision": route_decision_to_dict(decision),
        "run": director_run_to_dict(run),
    }


def server_version() -> dict[str, Any]:
    return {
        "mcp": f"@cubiczan/strata-mcp (strata {__version__})",
        "brand": "Cubiczan",
        "engine": "strata",
        "strata_version": __version__,
        "note": (
            "CHP is the lock; MCP is the pipe. "
            "This server wraps Strata — it does not rebuild the OS."
        ),
    }
