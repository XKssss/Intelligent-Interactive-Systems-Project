"""Model: a deterministic symbolic parser.

This component represents the inference/reasoning stage of the interaction
loop. It is intentionally rule-based rather than a hosted model so the
prototype runs with no API key and every interpretation is fully explainable.
A pluggable LLM adapter exposing the same interface is a planned extension
(see the README).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Vocabulary ---------------------------------------------------------------
COLORS = {"red", "blue", "green", "yellow", "white", "black"}
SHAPE_SYNONYMS = {"block": "cube", "ball": "sphere"}
SHAPES = {"cube", "sphere", "cylinder"}
SIZES = {"big", "large", "small", "little"}
SIZE_SYNONYMS = {"large": "big", "little": "small"}
DEICTIC_WORDS = {"this", "that", "it", "here", "there"}

SELECT_VERBS = {"select", "pick", "choose", "grab", "take"}
MOVE_VERBS = {"move", "put", "drag", "shift"}
REJECT_WORDS = {"no", "nope", "wrong", "not"}
CORRECTION_WORDS = {"actually", "instead", "mean", "said", "sorry", "correct"}

REPAIR_NONE = "none"
REPAIR_REJECT = "reject"
REPAIR_VERBAL_CORRECTION = "verbal_correction"


@dataclass
class ParseResult:
    intent: str = "unknown"
    color: str | None = None
    shape: str | None = None
    size: str | None = None
    deictic_word: bool = False
    repair_type: str = REPAIR_NONE
    confidence: float = 0.2
    tokens: list[str] = field(default_factory=list)

    @property
    def attributes(self) -> dict:
        return {"color": self.color, "shape": self.shape, "size": self.size}

    def as_dict(self) -> dict:
        return {
            "intent": self.intent,
            "attributes": self.attributes,
            "deictic_word": self.deictic_word,
            "repair_type": self.repair_type,
            "confidence": round(self.confidence, 2),
        }


class SymbolicParser:
    """Maps an utterance to an intent, referential attributes and a repair type."""

    def parse(self, utterance: str) -> ParseResult:
        tokens = re.findall(r"[a-z]+", utterance.lower())
        result = ParseResult(tokens=tokens)
        token_set = set(tokens)

        # Intent -------------------------------------------------------------
        if "undo" in token_set:
            result.intent = "undo"
        elif "help" in token_set:
            result.intent = "help"
        elif "cancel" in token_set or "stop" in token_set:
            result.intent = "cancel"
        elif token_set & MOVE_VERBS:
            result.intent = "move"
        elif token_set & SELECT_VERBS:
            result.intent = "select"

        # Referential attributes --------------------------------------------
        for token in tokens:
            if token in COLORS:
                result.color = token
            elif token in SHAPES:
                result.shape = token
            elif token in SHAPE_SYNONYMS:
                result.shape = SHAPE_SYNONYMS[token]
            elif token in SIZES:
                result.size = SIZE_SYNONYMS.get(token, token)
            elif token in SIZE_SYNONYMS:
                result.size = SIZE_SYNONYMS[token]
            elif token in DEICTIC_WORDS:
                result.deictic_word = True

        if result.intent == "unknown" and (
                result.color or result.shape or result.size or result.deictic_word):
            # A bare referential expression such as "the blue one" is a select.
            result.intent = "select"

        # Repair classification ---------------------------------------------
        has_reject = bool(token_set & REJECT_WORDS)
        has_correction = bool(token_set & CORRECTION_WORDS)
        has_attributes = any((result.color, result.shape, result.size))
        if has_reject or has_correction:
            result.repair_type = (
                REPAIR_VERBAL_CORRECTION if has_attributes else REPAIR_REJECT)

        # Confidence ---------------------------------------------------------
        attribute_count = sum(1 for value in result.attributes.values() if value)
        base = {0: 0.35, 1: 0.7, 2: 0.85, 3: 0.95}[attribute_count]
        if result.deictic_word:
            base = min(0.95, base + 0.1)
        result.confidence = base
        return result
