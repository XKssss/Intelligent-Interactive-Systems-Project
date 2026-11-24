"""Tools: bounded external capabilities that act on the BlockWorld.

Tools are the only component allowed to change the environment, and every
tool call is validated. This keeps the autonomy boundary explicit: the agent
may plan, but only these named actions can execute, and the user can undo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Fixed drop zone used by the move tool in this prototype.
DROP_ZONE = {"x": 150, "y": 120}


@dataclass
class ToolResult:
    name: str
    success: bool
    message: str
    target_id: str | None = None
    detail: dict[str, Any] | None = None

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "success": self.success,
            "message": self.message,
            "target_id": self.target_id,
            "detail": self.detail,
        }


def execute(world, tool: str, target_id: str,
            tool_args: dict | None = None) -> ToolResult:
    tool_args = tool_args or {}
    if tool == "select":
        success, message = world.select(target_id)
    elif tool == "move":
        success, message = world.move(
            target_id,
            tool_args.get("x", DROP_ZONE["x"]),
            tool_args.get("y", DROP_ZONE["y"]))
    else:
        return ToolResult(tool, False, f"Unknown tool '{tool}'.", target_id)
    return ToolResult(tool, success, message, target_id, tool_args)


def undo(world) -> ToolResult:
    success, message = world.undo()
    return ToolResult("undo", success, message)
