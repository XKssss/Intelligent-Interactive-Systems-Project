# RepairAgent

**README prose word count: 401** (excluding headings, code and setup commands)

## Project status

RepairAgent is a repair-aware multimodal conversational agent for a referential
block-world task. It is the prototype developed from the Assignment 1 literature
review on user-initiated multimodal repair.

**Implemented**

- The full interaction loop: sensing, parsing, planning, tool actions, feedback and memory
- A symbolic parser that recognises intents, referential attributes and repair moves
- User-initiated repair: repeat, reject, verbal correction, deictic repair, composite speech-plus-pointing repair, and clarification answers
- A single-page web interface with an inspectable system-understanding panel, repair history and transcript export
- Undo for every action and an explicit autonomy boundary

**Simulated**

- The verbal channel accepts typed text; the browser Web Speech API provides real speech-to-text where supported
- Pointing and gaze are simulated by clicking objects, with a modality toggle

**Planned**

- A pluggable LLM adapter behind the same parser interface, using an API key supplied by the reviewer
- Real eye-tracking input and additional task types

## Technology stack

- Python 3.10+ standard library only: `http.server` for the API and static hosting, `dataclasses` for the domain model
- HTML, CSS and vanilla JavaScript for the interface; Web Speech API for optional voice input
- No external Python packages are required

## Running the work

```
python run.py
```

Then open http://127.0.0.1:8000.

Other inspection options:

```
python -m tests.test_scenarios
python demo_walkthrough.py
```

## Development record

- Stage 1: built the BlockWorld ground truth and bounded select/move tools
- Stage 2: added multimodal sensing and fusion, then working and episodic memory
- Stage 3: implemented the symbolic parser and the repair state machine covering the repair repertoire identified in Assignment 1
- Stage 4: added the planner so ambiguous interpretations raise a clarification instead of executing
- Stage 5: built the web interface and the inspectable understanding panel, following the SOVITE transparency principle
- Stage 6: added scenario tests and the non-interactive walkthrough; fixed classification of implicit composite repair when a user redirects a selection by pointing

## AI assistance

AI was used to help draft and refactor code and to prepare this README. Every
generated component was reviewed, run locally and corrected, including the
repair classification logic and the planner flow. The design choices, claims and
references are the author's responsibility.

## API keys and additional files

No API keys are needed for the current prototype, and no keys are committed. The
planned LLM adapter will read a key from a local environment variable that
reviewers supply themselves. The Assignment 1 report and the final project report
are kept outside this repository as separate documents.
