# Publish checklist — Strata MCP wedge

Packaging for **later** publish as [`@cubiczan/strata-mcp`](https://www.npmjs.com/package/@cubiczan/strata-mcp).
**Do not npm or PyPI publish from a routine agent run.** Brand is **Cubiczan** (never CubicZan).

CHP is the lock; MCP is the pipe. This directory is the pipe's npm face.
The engine stays in `src/strata` (`python -m strata.mcp`).

## 1) npm (human OTP — not this run)

```bash
cd mcp
npm whoami          # expect: cubiczan
npm run build
npm publish --access public
npm view @cubiczan/strata-mcp version
```

## 2) Official MCP Registry (after npm)

```bash
mcp-publisher login github
mcp-publisher publish
# → io.github.cubiczan/strata-mcp
```

`mcpName` / `server.json` are ready; keep `package.json` version, `server.json`
version, and `server.json.packages[0].version` in lockstep (CHP MCP CI pattern).

## 3) Cursor / Claude one-liners (after npm)

```json
{
  "mcpServers": {
    "strata": { "command": "npx", "args": ["-y", "@cubiczan/strata-mcp"] }
  }
}
```

```bash
claude mcp add strata -- npx -y @cubiczan/strata-mcp
```

Until publish, use the Python entrypoint (see the repo README).

## Already done in-repo

- [x] stdio MCP wrapping real `MaturityAssessor` / `plan_90_days` / `Director`
- [x] Cursor `mcp.json` + `claude mcp add` docs
- [x] tests: tools/list + assessment/roadmap against `samples/`
- [ ] npm publish `@cubiczan/strata-mcp` (not this run)
- [ ] MCP Registry publish (not this run)
