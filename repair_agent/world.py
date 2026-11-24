"""BlockWorld: the simulated environment and ground truth for the referential task.

The scene contains blocks with observable properties (colour, shape, size and
position). Tool actions are validated against this ground truth and every
action is logged so it can be undone and inspected afterwards.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Block:
    id: str
    color: str
    shape: str
    size: str
    x: int
    y: int

    @property
    def label(self) -> str:
        return f"{self.size} {self.color} {self.shape}"


@dataclass
class ActionRecord:
    name: str
    target_id: Optional[str]
    detail: dict
    undone: bool = False


# A scene deliberately containing more than one red cube and more than one
# small object, so referential ambiguity and repair arise naturally.
DEFAULT_BLOCKS = [
    Block("b1", "red", "cube", "big", 40, 40),
    Block("b2", "red", "cube", "small", 180, 50),
    Block("b3", "blue", "sphere", "big", 320, 60),
    Block("b4", "green", "cylinder", "big", 60, 180),
    Block("b5", "red", "sphere", "small", 200, 190),
    Block("b6", "blue", "cube", "small", 340, 200),
]


class BlockWorld:
    """Holds the objects and applies the bounded tool actions."""

    def __init__(self, blocks: Optional[list[Block]] = None) -> None:
        blocks = blocks or DEFAULT_BLOCKS
        self.blocks: dict[str, Block] = {b.id: b for b in blocks}
        self.selected_id: Optional[str] = None
        self.action_log: list[ActionRecord] = []

    # ------------------------------------------------------------------ state
    def snapshot(self) -> dict:
        return {
            "blocks": [asdict(block) for block in self.blocks.values()],
            "selected_id": self.selected_id,
        }

    def get(self, block_id: str) -> Optional[Block]:
        return self.blocks.get(block_id)

    def find(self, color: Optional[str] = None, shape: Optional[str] = None,
             size: Optional[str] = None) -> list[Block]:
        """Return all blocks matching the given non-None attributes."""
        constraints = {"color": color, "shape": shape, "size": size}
        results = []
        for block in self.blocks.values():
            if all(value is None or getattr(block, attr) == value
                   for attr, value in constraints.items()):
                results.append(block)
        return results

    # ------------------------------------------------------------- tool actions
    def select(self, block_id: str) -> tuple[bool, str]:
        block = self.blocks.get(block_id)
        if block is None:
            return False, f"Object '{block_id}' does not exist."
        self.selected_id = block_id
        self.action_log.append(ActionRecord("select", block_id, {}))
        return True, f"Selected the {block.label}."

    def move(self, block_id: str, x: int, y: int) -> tuple[bool, str]:
        block = self.blocks.get(block_id)
        if block is None:
            return False, f"Object '{block_id}' does not exist."
        previous = {"x": block.x, "y": block.y}
        block.x, block.y = int(x), int(y)
        self.action_log.append(
            ActionRecord("move", block_id, {"from": previous,
                                            "to": {"x": block.x, "y": block.y}}))
        return True, f"Moved the {block.label} to ({block.x}, {block.y})."

    def clear_selection(self) -> tuple[bool, str]:
        self.selected_id = None
        self.action_log.append(ActionRecord("clear_selection", None, {}))
        return True, "Cleared the selection."

    def undo(self) -> tuple[bool, str]:
        """Reverse the most recent action that has not already been undone."""
        for record in reversed(self.action_log):
            if record.undone:
                continue
            if record.name == "select" and record.target_id == self.selected_id:
                self.selected_id = None
            elif record.name == "move":
                block = self.blocks.get(record.target_id)
                if block is not None:
                    block.x = record.detail["from"]["x"]
                    block.y = record.detail["from"]["y"]
            record.undone = True
            return True, f"Undid {record.name}."
        return False, "Nothing to undo."
