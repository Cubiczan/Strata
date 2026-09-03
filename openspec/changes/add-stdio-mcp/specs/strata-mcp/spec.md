# strata-mcp

Stdio MCP pipe for Cubiczan Strata. CHP is the lock; MCP is the pipe.

## Requirements

### Requirement: wrap real entrypoints

The server SHALL expose tools that call existing Strata APIs
(`MaturityAssessor`, `CompetencyAssessor`, `plan_90_days`, `Director`,
`registry.load_all`, `all_chains`). It SHALL NOT invent rubric items or
chain IDs that are not in the repository.

#### Scenario: assessment against fixture data

- GIVEN `samples/maturity_self_assessment.yaml`
- WHEN a client calls `assess_maturity`
- THEN the result SHALL include the fixture `target_id` and a function-axis heatmap
  produced by `MaturityAssessor`

#### Scenario: roadmap against fixture data

- GIVEN the same fixture
- WHEN a client calls `plan_90_day_roadmap`
- THEN the result SHALL include the three shipped phases (Days 1-30 / 31-60 / 61-90)

### Requirement: stdio MCP

The server SHALL start on stdio, answer `tools/list`, and accept `tools/call`.

#### Scenario: tools/list

- WHEN a client lists tools
- THEN the list SHALL include `assess_maturity` and `plan_90_day_roadmap`

### Requirement: install docs

The README SHALL document Cursor `mcp.json` and `claude mcp add`, and SHALL
spell the brand Cubiczan.
