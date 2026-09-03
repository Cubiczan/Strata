"""JSON-safe views of Strata dataclasses. No new scoring logic."""
from __future__ import annotations

from typing import Any

from strata.deliverable.factory import FactoryResult
from strata.maturity.assessor import AssessmentResult
from strata.maturity.roadmap import Roadmap
from strata.orchestrator.chains import Chain
from strata.orchestrator.director import DirectorRun, RouteDecision
from strata.schema import Rubric


def verdict_for(pct: float) -> str:
    if pct < 50:
        return "weak"
    if pct < 70:
        return "developing"
    return "mature"


def assessment_to_dict(result: AssessmentResult) -> dict[str, Any]:
    return {
        "target_id": result.target_id,
        "overall_pct": result.overall_pct,
        "heatmap": [
            {"name": name, "score_pct": pct, "verdict": verdict_for(pct)}
            for name, pct in result.heatmap()
        ],
        "capabilities": [
            {
                "rubric_id": snap.rubric.rubric_id,
                "name": snap.name,
                "score_pct": snap.score_pct,
                "weighted_total": snap.report.weighted_total,
                "normalized_pct": snap.report.normalized_pct,
                "passed": snap.report.passed,
                "scores": [s.model_dump() for s in snap.report.scores],
            }
            for snap in result.capabilities
        ],
    }


def roadmap_to_dict(roadmap: Roadmap) -> dict[str, Any]:
    return {
        "target_id": roadmap.target_id,
        "axis": roadmap.axis,
        "overall_pct": roadmap.overall_pct,
        "phases": [
            {
                "label": phase.label,
                "intent": phase.intent,
                "actions": [
                    {
                        "capability_id": action.capability_id,
                        "capability_name": action.capability_name,
                        "score_pct": action.score_pct,
                        "action": action.action,
                        "chain_id": action.chain_id,
                        "deliverable_rubric_id": action.deliverable_rubric_id,
                    }
                    for action in phase.actions
                ],
            }
            for phase in roadmap.phases
        ],
    }


def chain_to_dict(chain: Chain) -> dict[str, Any]:
    return {
        "chain_id": chain.chain_id,
        "rubric_id": chain.rubric_id,
        "depends_on": list(chain.depends_on),
        "steps": [
            {"skill_id": step.skill_id, "description": step.description}
            for step in chain.steps
        ],
    }


def rubric_summary(rubric: Rubric) -> dict[str, Any]:
    return {
        "rubric_id": rubric.rubric_id,
        "scope": rubric.scope,
        "name": rubric.name,
        "version": rubric.version,
        "groups": len(rubric.groups),
        "max_score": rubric.max_score,
    }


def factory_result_to_dict(result: FactoryResult) -> dict[str, Any]:
    return {
        "target_id": result.target_id,
        "rubric_id": result.rubric_id,
        "iterations": result.iterations,
        "passed": result.passed,
        "final_draft": result.final_draft,
        "final_score": {
            "weighted_total": result.final_report.report.weighted_total,
            "normalized_pct": result.final_report.report.normalized_pct,
            "passed": result.final_report.report.passed,
            "scores": [s.model_dump() for s in result.final_report.report.scores],
        },
        "history": [
            {
                "weighted_total": grade.report.weighted_total,
                "normalized_pct": grade.report.normalized_pct,
                "passed": grade.report.passed,
            }
            for grade in result.history
        ],
    }


def director_run_to_dict(run: DirectorRun) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "chain_id": run.chain_id,
        **factory_result_to_dict(run.factory_result),
    }


def route_decision_to_dict(decision: RouteDecision) -> dict[str, Any]:
    return {
        "chain_id": decision.chain.chain_id,
        "rubric_id": decision.chain.rubric_id,
        "weakest_capability": decision.weakest_capability,
        "weakest_pct": decision.weakest_pct,
        "rationale": decision.rationale,
        "preferred_signal": decision.preferred_signal,
        "alternates": [c.chain_id for c in decision.alternates],
    }
