"""Load a self-assessment YAML into an AssessmentResult.

Shared by the Typer CLI and the stdio MCP server so both wrap the same
L1 entrypoints (MaturityAssessor / CompetencyAssessor) without duplicating
the YAML → CharacteristicScore mapping.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from strata.maturity.assessor import CAPABILITY_RUBRIC_IDS, AssessmentResult, MaturityAssessor
from strata.maturity.competency import COMPETENCY_RUBRIC_IDS, CompetencyAssessor
from strata.schema import CharacteristicScore

VALID_AXES: tuple[str, ...] = ("function", "competency")
VALID_AXES_WITH_BOTH: tuple[str, ...] = ("function", "competency", "both")


def scores_from_mapping(
    raw: dict[str, Any],
    rubric_ids: tuple[str, ...],
    source: str,
) -> dict[str, list[CharacteristicScore]]:
    """Map ``{rubric_id: {characteristic_id: score}}`` to grader inputs.

    Raises ValueError (not KeyError) when a required rubric is missing, matching
    the CLI's historical "missing scores for rubric '...'" wording.
    """
    by_rubric: dict[str, list[CharacteristicScore]] = {}
    for rid in rubric_ids:
        if rid not in raw:
            raise ValueError(f"missing scores for rubric '{rid}' in {source}")
        by_rubric[rid] = [
            CharacteristicScore(characteristic_id=cid, score=int(s), rationale="self-assessed")
            for cid, s in raw[rid].items()
        ]
    return by_rubric


def parse_self_assessment_yaml(text: str) -> dict[str, Any]:
    raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise ValueError("self-assessment must be a YAML mapping")
    return raw


def load_self_assessment_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"self-assessment file not found: {path}")
    return parse_self_assessment_yaml(path.read_text(encoding="utf-8"))


def load_assessment(raw: dict[str, Any], axis: str, source: str = "<inline>") -> AssessmentResult:
    """Score one axis of an already-parsed self-assessment mapping."""
    if axis not in VALID_AXES:
        raise ValueError(f"axis must be 'function' or 'competency', got '{axis}'")
    target_id = raw.get("target_id", "unnamed")
    if axis == "function":
        by_rubric = scores_from_mapping(raw, CAPABILITY_RUBRIC_IDS, source)
        return MaturityAssessor().assess(target_id=target_id, scores_by_rubric=by_rubric)
    by_rubric = scores_from_mapping(raw, COMPETENCY_RUBRIC_IDS, source)
    return CompetencyAssessor().assess(target_id=target_id, scores_by_rubric=by_rubric)


def load_assessment_file(path: Path, axis: str = "function") -> AssessmentResult:
    raw = load_self_assessment_file(path)
    return load_assessment(raw, axis=axis, source=str(path))
