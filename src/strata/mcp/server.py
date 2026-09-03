"""Strata stdio MCP server — thin transport over the real OS entrypoints.

Pattern matches ``@cubiczan/chp-mcp``: Cursor / Claude Code speak MCP; this
process is the pipe; ``strata.maturity`` / ``strata.orchestrator`` are the lock.
"""
from __future__ import annotations

from typing import Any, Literal

from strata import __version__
from strata.mcp import tools as strata_tools

try:
    from mcp.server.mcpserver import MCPServer
except ImportError as exc:  # pragma: no cover - exercised only when extra missing
    raise ImportError(
        "install with `pip install -e '.[mcp]'` to use the Strata MCP server"
    ) from exc


def create_server() -> MCPServer[Any]:
    server = MCPServer(
        name="strata-mcp",
        title="Cubiczan Strata",
        description=(
            "CFO maturity assessment, rubric-graded deliverable chains, and a "
            "90-day roadmap. Wraps the Strata OS — does not invent rubric items."
        ),
        version=__version__,
        website_url="https://github.com/Cubiczan/Strata",
        instructions=(
            "Cubiczan Strata MCP. CHP is the lock; MCP is the pipe. "
            "Call assess_maturity and plan_90_day_roadmap against a self-assessment "
            "YAML (see samples/maturity_self_assessment.yaml). Call list_chains / "
            "run_chain to fetch and score shipped deliverable chains. "
            "Do not invent rubric IDs — use list_rubrics."
        ),
    )

    @server.tool(
        name="assess_maturity",
        title="Assess CFO maturity",
        description=(
            "Run the Strata L1 maturity assessor on a self-assessment YAML. "
            "Scores the function axis (8 process capabilities) and/or the "
            "competency axis (5 strategic-CFO pillars) using rubrics already "
            "in the repo. Returns heatmaps, verdicts, and characteristic scores."
        ),
    )
    def assess_maturity(
        self_assessment_path: str | None = None,
        self_assessment_yaml: str | None = None,
        axis: Literal["function", "competency", "both"] = "both",
    ) -> dict[str, Any]:
        return strata_tools.assess_maturity(
            self_assessment_path=self_assessment_path,
            self_assessment_yaml=self_assessment_yaml,
            axis=axis,
        )

    @server.tool(
        name="plan_90_day_roadmap",
        title="Generate 90-day roadmap",
        description=(
            "Generate the Strata 90-day phased roadmap (Baseline / Scale / Embed) "
            "from a self-assessment via plan_90_days. Actions point at shipped "
            "deliverable chains when a capability has one."
        ),
    )
    def plan_90_day_roadmap(
        self_assessment_path: str | None = None,
        self_assessment_yaml: str | None = None,
        axis: Literal["function", "competency"] = "function",
    ) -> dict[str, Any]:
        return strata_tools.plan_90_day_roadmap(
            self_assessment_path=self_assessment_path,
            self_assessment_yaml=self_assessment_yaml,
            axis=axis,
        )

    @server.tool(
        name="list_chains",
        title="List deliverable chains",
        description=(
            "Fetch every registered deliverable chain (chain_id, rubric_id, "
            "steps, depends_on). IDs come from the in-repo chain registry."
        ),
    )
    def list_chains() -> dict[str, Any]:
        return strata_tools.list_registered_chains()

    @server.tool(
        name="run_chain",
        title="Score a deliverable chain",
        description=(
            "Run Director.run_chain for a registered chain_id and return the "
            "rubric-graded draft (mock author/grader unless use_llm is true). "
            "Use list_chains for valid IDs. Sample inputs live under samples/."
        ),
    )
    def run_chain(
        chain_id: str,
        inputs: dict[str, Any] | None = None,
        inputs_path: str | None = None,
        use_llm: bool = False,
        persist: bool = False,
    ) -> dict[str, Any]:
        return strata_tools.run_deliverable_chain(
            chain_id=chain_id,
            inputs=inputs,
            inputs_path=inputs_path,
            use_llm=use_llm,
            persist=persist,
        )

    @server.tool(
        name="route_chain",
        title="Route and score weakest-capability chain",
        description=(
            "Director.route: pick the chain that targets the weakest assessed "
            "capability, then score it. Optional inputs.preferred_deliverable "
            "selects among candidates for that capability."
        ),
    )
    def route_chain(
        self_assessment_path: str | None = None,
        self_assessment_yaml: str | None = None,
        inputs: dict[str, Any] | None = None,
        inputs_path: str | None = None,
        axis: Literal["function", "competency"] = "function",
        use_llm: bool = False,
        persist: bool = False,
    ) -> dict[str, Any]:
        return strata_tools.route_and_run_deliverable(
            self_assessment_path=self_assessment_path,
            self_assessment_yaml=self_assessment_yaml,
            inputs=inputs,
            inputs_path=inputs_path,
            axis=axis,
            use_llm=use_llm,
            persist=persist,
        )

    @server.tool(
        name="list_rubrics",
        title="List shipped rubrics",
        description=(
            "List every rubric loaded from src/strata/rubrics (function, "
            "competency, deliverable). Does not invent rubric items."
        ),
    )
    def list_rubrics() -> dict[str, Any]:
        return strata_tools.list_registered_rubrics()

    @server.tool(
        name="strata_version",
        title="Strata MCP version",
        description="Report MCP server, brand (Cubiczan), and Strata engine versions.",
    )
    def strata_version() -> dict[str, Any]:
        return strata_tools.server_version()

    return server


def main() -> None:
    from strata.observability import init_observability

    init_observability("strata-mcp")
    create_server().run(transport="stdio")
