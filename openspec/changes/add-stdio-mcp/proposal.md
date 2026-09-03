# Change: add-stdio-mcp

Add a stdio MCP server so Cursor and Claude Code can call Strata's existing
CFO maturity assessment, rubric-graded deliverable chains, and 90-day roadmap.

## Why

Agents already speak MCP. Strata's behavior lives in Python
(`MaturityAssessor`, `plan_90_days`, `Director`). A thin pipe — same shape as
`@cubiczan/chp-mcp` — exposes those entrypoints without rebuilding the OS.

## What changes

- Shared YAML loader used by CLI and MCP (`strata.maturity.load`)
- `python -m strata.mcp` / `strata-mcp` stdio server
- Tools wrap real entrypoints only; rubric IDs stay in-repo
- `mcp/` packaging for later `@cubiczan/strata-mcp` npm publish (not this run)
- README: Cursor `mcp.json` and `claude mcp add`

## Out of scope

- Reimplementing assessment, grading, or roadmap logic
- Inventing rubric items or chain IDs
- npm / PyPI publish from this change
