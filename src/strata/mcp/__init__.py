"""Stdio MCP pipe for Strata.

CHP is the lock; MCP is the pipe. This package wraps the real L1 assessor,
L4 deliverable factory, and ``plan_90_days`` entrypoints — it does not
rebuild the OS or invent rubric items.
"""
from __future__ import annotations

from typing import Any

__all__ = ["create_server", "main"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from strata.mcp.server import create_server, main

        return create_server if name == "create_server" else main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
