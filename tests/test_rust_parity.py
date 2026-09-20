"""Row 14 parity fixtures: Python and Rust rubric scoring must agree.

The Python `RubricScoreReport.compute` in `src/strata/schema.py` is the
maintained implementation; `rust/src/lib.rs::compute_rubric_score`
independently implements the same weighted math, reachable through the
`strata.rust_core.run_strata_core` stdio bridge. These fixtures pin the same
rubric + scores through both paths and fail loudly on divergence. Skipped
with an explicit reason when cargo is unavailable.
"""

from __future__ import annotations

import shutil

import pytest

from strata import rust_core
from strata.schema import (
    Attribute,
    Characteristic,
    CharacteristicScore,
    Group,
    Rubric,
    RubricScoreReport,
)

pytestmark = pytest.mark.skipif(
    shutil.which("cargo") is None, reason="cargo unavailable; cannot build strata-core"
)

TOL = 1e-9


def _rubric() -> Rubric:
    return Rubric(
        rubric_id="rb.parity.par1",
        scope="deliverable",
        name="Parity fixture rubric",
        version=1,
        groups=(
            Group(
                id="analysis",
                name="Analysis",
                weight=0.6,
                characteristics=(
                    Characteristic(
                        id="depth",
                        name="Depth",
                        weight=0.5,
                        attributes=(
                            Attribute(level="Strong", score=4, anchor="Exhaustive"),
                            Attribute(level="Weak", score=1, anchor="Thin"),
                        ),
                    ),
                    Characteristic(
                        id="accuracy",
                        name="Accuracy",
                        weight=0.5,
                        attributes=(
                            Attribute(level="Strong", score=3, anchor="Exact"),
                            Attribute(level="Weak", score=0, anchor="Wrong"),
                        ),
                    ),
                ),
            ),
            Group(
                id="delivery",
                name="Delivery",
                weight=0.4,
                characteristics=(
                    Characteristic(
                        id="clarity",
                        name="Clarity",
                        weight=1.0,
                        attributes=(
                            Attribute(level="Strong", score=3, anchor="Clear"),
                            Attribute(level="Weak", score=0, anchor="Muddled"),
                        ),
                    ),
                ),
            ),
        ),
    )


def _scores(depth: int, accuracy: int, clarity: int) -> list[CharacteristicScore]:
    return [
        CharacteristicScore(characteristic_id="depth", score=depth, rationale="fixture"),
        CharacteristicScore(characteristic_id="accuracy", score=accuracy, rationale="fixture"),
        CharacteristicScore(characteristic_id="clarity", score=clarity, rationale="fixture"),
    ]


def _rust_report(rubric: Rubric, target_id: str, scores: list[CharacteristicScore],
                 threshold: float = 70.0) -> dict:
    payload = {
        "rubric": rubric.model_dump(mode="json"),
        "target_id": target_id,
        "scores": [s.model_dump() for s in scores],
        "pass_threshold_pct": threshold,
    }
    response = rust_core.run_strata_core("compute_rubric_score", payload)
    assert response["kind"] == "rubric_score_report", response
    return response["value"]


def test_python_and_rust_agree_on_pass_case() -> None:
    rubric = _rubric()
    scores = _scores(4, 2, 3)  # 0.6*0.5*4 + 0.6*0.5*2 + 0.4*1.0*3 = 3.0 -> 75%

    report = RubricScoreReport.compute(rubric, "parity-target", scores)
    assert (report.weighted_total, report.normalized_pct) == (3.0, 75.0)
    assert report.passed is True

    rs = _rust_report(rubric, "parity-target", scores)
    assert rs["weighted_total"] == pytest.approx(3.0, abs=TOL)
    assert rs["normalized_pct"] == pytest.approx(75.0, abs=TOL)
    assert rs["passed"] is True


def test_python_and_rust_agree_on_fail_case() -> None:
    rubric = _rubric()
    scores = _scores(1, 1, 1)  # 0.3 + 0.3 + 0.4 = 1.0 -> 25%

    report = RubricScoreReport.compute(rubric, "parity-target", scores)
    assert (report.weighted_total, report.normalized_pct) == (1.0, 25.0)
    assert report.passed is False

    rs = _rust_report(rubric, "parity-target", scores)
    assert rs["weighted_total"] == pytest.approx(1.0, abs=TOL)
    assert rs["normalized_pct"] == pytest.approx(25.0, abs=TOL)
    assert rs["passed"] is False


def test_python_and_rust_agree_at_threshold_boundary() -> None:
    rubric = _rubric()
    scores = _scores(4, 1, 2)  # 1.2 + 0.3 + 0.8 = 2.3 -> 57.49999999999999 in IEEE doubles

    # Both implementations compute the same f64 arithmetic in the same order, so
    # a 57.5 threshold does NOT pass (57.499...% < 57.5) — pin that shared
    # boundary semantics rather than naive decimal expectations.
    report = RubricScoreReport.compute(rubric, "parity-target", scores, 57.5)
    assert report.normalized_pct == pytest.approx(57.5, abs=TOL)
    assert report.passed is False

    rs = _rust_report(rubric, "parity-target", scores, 57.5)
    assert rs["normalized_pct"] == pytest.approx(57.5, abs=TOL)
    assert rs["passed"] is False
