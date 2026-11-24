"""Planning/decision: converts a parse into a bounded action, clarification or
message. The planner never touches the world directly; it only returns a
Decision, which the agent executes through the named tools.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import repair as repair_types
from .model import REPAIR_NONE, REPAIR_REJECT, REPAIR_VERBAL_CORRECTION

HELP_TEXT = (
    "Ask me to select or move an object by describing it, for example "
    "'select the big red cube'. You can also click an object to point at it, "
    "say 'no' to reject my interpretation, describe the correct object, or "
    "say 'undo' to reverse the last action."
)


@dataclass
class Decision:
    kind: str  # act | clarify | confirm | message | undo | cancel
    tool: str | None = None
    target_id: str | None = None
    candidates: list[str] = field(default_factory=list)
    tool_args: dict = field(default_factory=dict)
    message: str = ""
    repair_type: str = REPAIR_NONE

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "tool": self.tool,
            "target_id": self.target_id,
            "candidates": self.candidates,
            "tool_args": self.tool_args,
            "message": self.message,
            "repair_type": self.repair_type,
        }


class Planner:
    # ---------------------------------------------------------------- entry
    def decide(self, agent, observation, parse) -> Decision:
        world, memory, repairs = agent.world, agent.memory, agent.repairs
        deictic_id = observation.deictic.target_id if observation.deictic else None

        # Meta intents ------------------------------------------------------
        if parse.intent == "undo":
            return Decision("undo", message="Reversing the last action.")
        if parse.intent == "help":
            return Decision("message", message=HELP_TEXT)
        if parse.intent == "cancel":
            if memory.awaiting_clarification:
                memory.resolve_clarification()
            return Decision("cancel", message="Cancelled. What would you like to do?")

        # Pending clarification: this turn is an answer ---------------------
        if memory.awaiting_clarification:
            return self._answer_clarification(agent, observation, parse, deictic_id)

        # Repeat -------------------------------------------------------------
        if repairs.is_repeat(observation.normalized_utterance) and not deictic_id:
            if memory.last_target_id:
                return self._action(
                    memory.last_intent or "select", memory.last_target_id,
                    repair_types.REPEAT, "Repeating your last request.")
            return Decision("message", message="I have no previous request to repeat.")

        # Classify any repair in the current turn ---------------------------
        current_repair = self._classify_repair(observation, parse, deictic_id, memory)
        if current_repair is None:
            return Decision("message",
                            message="Point at an object and tell me what to do with it.")

        # Deictic fusion: a pointed object always resolves the referent -----
        if deictic_id is not None:
            if world.get(deictic_id) is None:
                return Decision("message", message="I could not locate that object.")
            tool = parse.intent if parse.intent in ("select", "move") else \
                memory.last_intent or "select"
            note = ("Fusing your speech with the pointed object."
                    if current_repair == REPAIR_NONE else
                    "Applying your multimodal repair.")
            return self._action(tool, deictic_id, current_repair, note)

        # Verbal resolution -------------------------------------------------
        if parse.repair_type == REPAIR_REJECT:
            return Decision("message",
                            message="Understood. What would you like instead?")

        candidates = world.find(**parse.attributes)
        if not candidates:
            return Decision("message",
                            message="I cannot find an object matching that description.")
        if len(candidates) > 1:
            return self._clarify(memory, parse, candidates)

        target = candidates[0]
        if parse.confidence < 0.5:
            return Decision("confirm", target_id=target.id,
                            candidates=[target.id],
                            message=f"Did you mean the {target.label}? Please confirm.")
        return self._action(parse.intent, target.id, current_repair,
                            f"Acting on the {target.label}.")

    # ------------------------------------------------------------- internals
    def _answer_clarification(self, agent, observation, parse, deictic_id) -> Decision:
        memory, world = agent.memory, agent.world
        pending_ids = memory.pending_clarification
        memory.resolve_clarification()
        tool = memory.last_intent or "select"

        if deictic_id is not None:
            if deictic_id in pending_ids:
                return self._action(tool, deictic_id,
                                    repair_types.CLARIFICATION_ANSWER,
                                    "Using your point to resolve the clarification.")
            return Decision("message",
                            message="That object was not one of the options.")

        matched = [block for block in world.find(**parse.attributes)
                   if block.id in pending_ids]
        if len(matched) == 1:
            return self._action(tool, matched[0].id,
                                repair_types.CLARIFICATION_ANSWER,
                                "Using your answer to resolve the clarification.")
        if not matched:
            memory.ask_clarification(pending_ids)
            return Decision("clarify", candidates=pending_ids,
                            message="Please choose one of the listed objects.")
        ids = [block.id for block in matched]
        memory.ask_clarification(ids)
        return Decision("clarify", candidates=ids,
                        message="That still matches more than one object; please choose.")

    def _classify_repair(self, observation, parse, deictic_id, memory):
        has_speech = bool(observation.utterance.strip())

        if parse.repair_type in (REPAIR_REJECT, REPAIR_VERBAL_CORRECTION):
            if deictic_id and has_speech:
                return repair_types.COMPOSITE
            if deictic_id:
                return repair_types.DEICTIC
            return (repair_types.VERBAL_CORRECTION
                    if parse.repair_type == REPAIR_VERBAL_CORRECTION
                    else repair_types.REJECT)

        if deictic_id:
            if has_speech:
                # Redirecting an existing selection to another object is an
                # implicit composite repair even without a word such as "no".
                if (memory.last_target_id and
                        memory.last_target_id != deictic_id):
                    return repair_types.COMPOSITE
                return REPAIR_NONE  # ordinary multimodal fusion
            if memory.last_target_id:
                return repair_types.DEICTIC
            return None
        return REPAIR_NONE

    def _clarify(self, memory, parse, candidates) -> Decision:
        ids = [block.id for block in candidates]
        memory.update_last_interpretation(parse.intent, parse.attributes, None)
        memory.ask_clarification(ids)
        labels = ", ".join(f"{block.id}: {block.label}" for block in candidates)
        return Decision("clarify", tool=parse.intent, candidates=ids,
                        message=f"I see more than one match ({labels}). Which do you mean?")

    def _action(self, tool, target_id, repair_type, note) -> Decision:
        if tool not in ("select", "move"):
            tool = "select"
        return Decision("act", tool=tool, target_id=target_id,
                        candidates=[target_id], repair_type=repair_type, message=note)
