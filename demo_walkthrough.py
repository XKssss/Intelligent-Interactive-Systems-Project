"""Non-interactive walkthrough of the developed interaction.

Runs scripted scenarios through the same agent loop used by the web
interface and prints a readable transcript. This is evidence that the
interaction works even without opening a browser:

    python demo_walkthrough.py
"""
from __future__ import annotations

from repair_agent.agent import RepairAgent

SCENARIOS = [
    ("Direct command", [
        {"utterance": "select the big red cube"},
    ]),
    ("Ambiguity resolved by pointing", [
        {"utterance": "select the red cube"},
        {"deictic_target": "b2", "deictic_modality": "point"},
    ]),
    ("Reject and verbal correction", [
        {"utterance": "select the big red cube"},
        {"utterance": "no, the blue sphere"},
    ]),
    ("Composite multimodal repair", [
        {"utterance": "select the red sphere"},
        {"utterance": "this one", "deictic_target": "b4",
         "deictic_modality": "gaze"},
    ]),
    ("Move and undo", [
        {"utterance": "move the big red cube"},
        {"utterance": "undo"},
    ]),
]


def main() -> None:
    for title, turns in SCENARIOS:
        print("=" * 70)
        print("SCENARIO:", title)
        agent = RepairAgent()
        for kwargs in turns:
            response = agent.handle(**kwargs)
            print(f"  Turn {response['turn_id']} channels={response['channels']}")
            print(f"    parsed={response['parse']}")
            print(f"    feedback: {response['feedback']}")
            if response["action"]:
                print(f"    action: {response['action'].get('message')}")
        print(f"  repairs in this scenario: {agent.repairs.repair_count}")
    print("=" * 70)
    print("Walkthrough complete.")


if __name__ == "__main__":
    main()
