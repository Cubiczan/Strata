#!/usr/bin/env node
/**
 * @cubiczan/strata-mcp — stdio pipe onto `python -m strata.mcp`.
 *
 * CHP is the lock; MCP is the pipe. This process does not reimplement
 * maturity scoring or invent rubric items — it execs the Strata engine.
 *
 *   npx -y @cubiczan/strata-mcp
 *
 * Requires the Strata Python package (`pip install -e ".[mcp]"` or the
 * published wheel) on PATH. Override the interpreter with STRATA_PYTHON.
 */

import { spawn } from "node:child_process";

const python = process.env.STRATA_PYTHON ?? "python3";
const child = spawn(python, ["-m", "strata.mcp"], {
  stdio: "inherit",
  env: process.env,
});

child.on("error", (err) => {
  console.error(
    `[strata-mcp] failed to start ${python} -m strata.mcp: ${err.message}\n` +
      `Install Strata with the MCP extra: pip install -e ".[mcp]"`,
  );
  process.exit(1);
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});

function shutdown(): void {
  if (!child.killed) {
    child.kill("SIGTERM");
  }
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
