"""Sensing: multimodal input events and their fusion.

Two input channels are represented:
  * the verbal channel (utterance text; in the web UI this can be typed or
    produced by the browser's Web Speech API, which is real speech-to-text),
  * the deictic channel (a click on an object, labelled as pointing or gaze).

A single observation can carry both channels at once, which is what allows
composite multimodal repair such as saying "no, this one" while pointing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

POINT = "point"
GAZE = "gaze"
SPEECH = "speech"


@dataclass
class DeicticEvent:
    target_id: str
    modality: str = POINT  # POINT or GAZE

    def as_dict(self) -> dict:
        return {"target_id": self.target_id, "modality": self.modality}


@dataclass
class Observation:
    turn_id: int
    utterance: str = ""
    deictic: Optional[DeicticEvent] = None

    @property
    def normalized_utterance(self) -> str:
        return " ".join(self.utterance.lower().split())

    def channels(self) -> list[str]:
        active = []
        if self.utterance.strip():
            active.append(SPEECH)
        if self.deictic is not None:
            active.append(self.deictic.modality)
        return active

    def is_empty(self) -> bool:
        return not self.utterance.strip() and self.deictic is None

    def as_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "utterance": self.utterance,
            "deictic": self.deictic.as_dict() if self.deictic else None,
            "channels": self.channels(),
        }
