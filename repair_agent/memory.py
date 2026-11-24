"""Context and memory: working state plus an episodic transcript.

Working memory holds the short-lived interaction state (a pending
clarification, the last interpretation and the last resolved target).
Episodic memory stores every turn so the interaction can be replayed and
exported, which is also the evidence used in the development record.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TurnRecord:
    turn_id: int
    observation: dict
    parse: dict
    decision: dict
    feedback: str
    action: dict

    def as_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "observation": self.observation,
            "parse": self.parse,
            "decision": self.decision,
            "feedback": self.feedback,
            "action": self.action,
        }


class Memory:
    def __init__(self) -> None:
        # Working memory ------------------------------------------------------
        self.pending_clarification: Optional[list[str]] = None
        self.last_intent: Optional[str] = None
        self.last_attributes: dict = {}
        self.last_target_id: Optional[str] = None
        # Episodic memory -----------------------------------------------------
        self.transcript: list[TurnRecord] = []

    # ------------------------------------------------------- working-memory API
    def ask_clarification(self, candidate_ids: list[str]) -> None:
        self.pending_clarification = list(candidate_ids)

    def resolve_clarification(self) -> None:
        self.pending_clarification = None

    @property
    def awaiting_clarification(self) -> bool:
        return self.pending_clarification is not None

    def update_last_interpretation(self, intent: str, attributes: dict,
                                   target_id: Optional[str]) -> None:
        self.last_intent = intent
        self.last_attributes = dict(attributes)
        if target_id is not None:
            self.last_target_id = target_id

    # ------------------------------------------------------ episodic-memory API
    def record_turn(self, turn_id: int, observation: dict, parse: dict,
                    decision: dict, feedback: str, action: dict) -> None:
        self.transcript.append(
            TurnRecord(turn_id, observation, parse, decision, feedback, action))

    def transcript_as_list(self) -> list[dict]:
        return [record.as_dict() for record in self.transcript]

    def clear(self) -> None:
        self.pending_clarification = None
        self.last_intent = None
        self.last_attributes = {}
        self.last_target_id = None
        self.transcript = []
