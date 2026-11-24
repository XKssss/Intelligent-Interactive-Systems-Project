"""Agent orchestration: the sense - interpret - act - adapt loop.

One RepairAgent instance owns the world, memory, parser, repair tracker and
planner, and returns a fully explainable response for every turn.
"""
from __future__ import annotations

from . import tools
from .memory import Memory
from .model import REPAIR_NONE, SymbolicParser
from .planner import Planner
from .repair import RepairTracker
from .sensing import DeicticEvent, Observation
from .world import BlockWorld

AUTONOMY_BOUNDARY = (
    "The agent executes select/move actions only when it resolves a single "
    "referent; ambiguous or low-confidence interpretations are returned to "
    "the user for clarification, and every action can be undone."
)


class RepairAgent:
    def __init__(self, world: BlockWorld | None = None) -> None:
        self.world = world or BlockWorld()
        self.memory = Memory()
        self.parser = SymbolicParser()
        self.planner = Planner()
        self.repairs = RepairTracker()
        self.turn_id = 0

    def reset(self) -> None:
        self.__init__()

    def handle(self, utterance: str = "", deictic_target: str | None = None,
               deictic_modality: str = "point") -> dict:
        self.turn_id += 1
        deictic = (DeicticEvent(deictic_target, deictic_modality)
                   if deictic_target else None)
        observation = Observation(self.turn_id, utterance, deictic)
        if observation.is_empty():
            return {"error": "empty observation", "state": self.world.snapshot()}

        parse = self.parser.parse(observation.utterance)
        decision = self.planner.decide(self, observation, parse)

        action: dict = {}
        if decision.kind == "act":
            result = tools.execute(self.world, decision.tool,
                                   decision.target_id, decision.tool_args)
            action = result.as_dict()
        elif decision.kind == "undo":
            action = tools.undo(self.world).as_dict()

        if decision.repair_type != REPAIR_NONE and action:
            self.repairs.record(decision.repair_type, observation.as_dict(),
                                action.get("message", decision.message))

        # Keep the last command intent for repeats and clarification answers.
        if parse.intent in ("select", "move"):
            self.memory.update_last_interpretation(
                parse.intent, parse.attributes, decision.target_id)
        self.memory.record_turn(self.turn_id, observation.as_dict(),
                                parse.as_dict(), decision.as_dict(),
                                decision.message, action)
        self.repairs.remember_utterance(observation.normalized_utterance)

        return {
            "turn_id": self.turn_id,
            "channels": observation.channels(),
            "parse": parse.as_dict(),
            "decision": decision.as_dict(),
            "action": action,
            "repair_count": self.repairs.repair_count,
            "repair_log": self.repairs.repair_log,
            "feedback": decision.message,
            "autonomy_boundary": AUTONOMY_BOUNDARY,
            "state": self.world.snapshot(),
        }
