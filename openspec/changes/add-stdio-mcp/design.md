# Design: stdio MCP pipe

## Pattern

`@cubiczan/chp-mcp` is the lock/pipe split: the MCP process is transport;
the engine stays in the published library. Strata's engine is Python, so:

```text
Cursor / Claude Code  --stdio JSON-RPC-->  python -m strata.mcp
                                              |
                                              v
                              MaturityAssessor / plan_90_days / Director
```

`@cubiczan/strata-mcp` (npm) execs that same module. It does not re-score.

## Tools

| Tool | Entrypoint |
|------|------------|
| `assess_maturity` | `load_assessment` + `MaturityAssessor` / `CompetencyAssessor` |
| `plan_90_day_roadmap` | `plan_90_days` |
| `list_chains` | `all_chains()` |
| `run_chain` | `Director.run_chain` |
| `route_chain` | `Director.route` |
| `list_rubrics` | `registry.load_all()` |
| `strata_version` | `strata.__version__` |

Fixtures: `samples/maturity_self_assessment.yaml`, `samples/*_inputs.json`.

## Tests

`tools/list` plus one `assess_maturity` or `plan_90_day_roadmap` call against
the sample self-assessment, over in-process MCP and real stdio.
