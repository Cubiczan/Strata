# `@cubiczan/strata-mcp`

Stdio MCP pipe for **[Cubiczan](https://github.com/Cubiczan) Strata** — CFO maturity
assessment, rubric-graded deliverable chains, and a 90-day roadmap.

CHP is the lock; MCP is the pipe. This package does **not** rebuild the OS or
invent rubric items. It execs `python -m strata.mcp`, which wraps
`MaturityAssessor`, `plan_90_days`, and `Director`.

Pattern: [`@cubiczan/chp-mcp`](https://www.npmjs.com/package/@cubiczan/chp-mcp).

## How the pieces fit

```text
MCP client (Cursor / Claude Code / …)
        │  tools/call
        ▼
┌───────────────────────────┐
│  MCP server (transport)   │  ← you are here (@cubiczan/strata-mcp)
│  assess_maturity          │
│  plan_90_day_roadmap      │
│  list_chains / run_chain  │
└─────────────┬─────────────┘
              │ wraps
              ▼
┌───────────────────────────┐
│  Strata OS (Python)       │
│  L1 assessor · L4 factory │
│  plan_90_days             │
└───────────────────────────┘
```

## Install

Requires the Strata Python package with the MCP extra (same repo):

```bash
pip install -e ".[mcp]"
# later, after npm publish:
npm install -g @cubiczan/strata-mcp
# or one-shot
npx -y @cubiczan/strata-mcp
```

### Cursor / Claude Desktop

```json
{
  "mcpServers": {
    "strata": {
      "command": "python",
      "args": ["-m", "strata.mcp"]
    }
  }
}
```

After npm publish:

```json
{
  "mcpServers": {
    "strata": {
      "command": "npx",
      "args": ["-y", "@cubiczan/strata-mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add strata -- python -m strata.mcp
# after publish:
claude mcp add strata -- npx -y @cubiczan/strata-mcp
```

## Tools

| Tool | Maps to | Purpose |
|------|---------|---------|
| `assess_maturity` | `MaturityAssessor` / `CompetencyAssessor` | Dual-axis CFO heatmap from a self-assessment YAML |
| `plan_90_day_roadmap` | `plan_90_days` | 90-day Baseline / Scale / Embed plan |
| `list_chains` | `all_chains()` | Fetch shipped deliverable chains |
| `run_chain` | `Director.run_chain` | Rubric-grade one chain (mock author by default) |
| `route_chain` | `Director.route` | Weakest-capability chain, then score it |
| `list_rubrics` | `registry.load_all()` | In-repo rubrics only — nothing invented |
| `strata_version` | — | Cubiczan / Strata versions |

Use `samples/maturity_self_assessment.yaml` and `samples/*_inputs.json` as fixtures.

## Licence

Proprietary (same as Strata). See the parent repo [NOTICE](../NOTICE).
