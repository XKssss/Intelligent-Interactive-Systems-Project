"""Repair state machine: recognises and logs user-initiated repair sequences.

Repair types covered (grounded in the Assignment 1 review):
  * repeat              - the user re-issues the same utterance,
  * reject              - "no" / "wrong" with no new description,
  * verbal_correction   - a new spoken description,
  * deictic_repair      - a pointing/gaze event used to correct,
  * composite_repair    - speech and deictic correction together,
  * clarification_answer- the user answers a system clarification.
"""
from __future__ import annotations

REPEAT = "repeat"
REJECT = "reject"
VERBAL_CORRECTION = "verbal_correction"
DEICTIC = "deictic_repair"
COMPOSITE = "composite_repair"
CLARIFICATION_ANSWER = "clarification_answer"


class RepairTracker:
    def __init__(self) -> None:
        self.repair_count = 0
        self.repair_log: list[dict] = []
        self._last_utterance: str = ""

    def is_repeat(self, normalized_utterance: str) -> bool:
        if not normalized_utterance:
            return False
        return normalized_utterance == self._last_utterance

    def remember_utterance(self, normalized_utterance: str) -> None:
        self._last_utterance = normalized_utterance

    def record(self, repair_type: str, observation: dict, resolution: str) -> dict:
        entry = {
            "index": self.repair_count + 1,
            "repair_type": repair_type,
            "channels": observation.get("channels", []),
            "resolution": resolution,
        }
        self.repair_count += 1
        self.repair_log.append(entry)
        return entry
