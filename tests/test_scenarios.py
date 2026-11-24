"""Scenario tests for the RepairAgent.

Run from the project root:
    python -m tests.test_scenarios
"""
from __future__ import annotations

from repair_agent.agent import RepairAgent

PASS = 0
FAIL = 0


def check(name: str, condition: bool) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}")


def run() -> None:
    # 1. Unambiguous direct command -----------------------------------------
    print("1. Direct command")
    agent = RepairAgent()
    response = agent.handle("select the big red cube")
    check("single resolved action", response["decision"]["kind"] == "act")
    check("target is b1", response["decision"]["target_id"] == "b1")
    check("action succeeded", response["action"].get("success") is True)

    # 2. Ambiguity -> clarification -> deictic answer -----------------------
    print("2. Ambiguity and clarification")
    response = agent.handle("select the red cube")
    check("clarification requested", response["decision"]["kind"] == "clarify")
    check("candidates b1 and b2", response["decision"]["candidates"] == ["b1", "b2"])
    response = agent.handle(deictic_target="b2")
    check("point resolves clarification", response["decision"]["kind"] == "act")
    check("resolved target b2", response["decision"]["target_id"] == "b2")
    check("logged as clarification answer",
          response["decision"]["repair_type"] == "clarification_answer")

    # 3. Reject then verbal correction --------------------------------------
    print("3. Verbal correction repair")
    agent = RepairAgent()
    agent.handle("select the big red cube")
    response = agent.handle("no, the blue sphere")
    check("verbal correction",
          response["decision"]["repair_type"] == "verbal_correction")
    check("corrected target b3", response["decision"]["target_id"] == "b3")

    # 4. Repeat --------------------------------------------------------------
    print("4. Repeat")
    agent = RepairAgent()
    agent.handle("select the blue sphere")
    response = agent.handle("select the blue sphere")
    check("repeat detected", response["decision"]["repair_type"] == "repeat")

    # 5. Composite deictic fusion --------------------------------------------
    print("5. Deictic fusion")
    agent = RepairAgent()
    response = agent.handle("this one", deictic_target="b3")
    check("pointed target b3", response["decision"]["target_id"] == "b3")
    check("both channels used", response["channels"] == ["speech", "point"])

    # 6. Move tool ------------------------------------------------------------
    print("6. Move tool")
    agent = RepairAgent()
    response = agent.handle("move the big red cube")
    check("move executed", response["action"].get("name") == "move")
    check("move succeeded", response["action"].get("success") is True)

    # 7. No matching object ---------------------------------------------------
    print("7. No match")
    agent = RepairAgent()
    response = agent.handle("select the yellow cylinder")
    check("message instead of action", response["decision"]["kind"] == "message")
    check("no action taken", response["action"] == {})

    # 8. Undo -----------------------------------------------------------------
    print("8. Undo")
    agent = RepairAgent()
    agent.handle("select the big red cube")
    response = agent.handle("undo")
    check("undo succeeded", response["action"].get("success") is True)
    check("selection cleared", agent.world.selected_id is None)

    print(f"\n{PASS} passed, {FAIL} failed")
    if FAIL:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
