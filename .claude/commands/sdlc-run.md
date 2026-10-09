---
description: Orchestrate the full 8-step Agentic SDLC for DS-1, halting at every human gate.
---

Act as the **Agentic SDLC orchestrator** for this repository.

1. Read `CLAUDE.md` and `.claude/AGENTIC_SDLC_PROCESS.md`.
2. Run `/sdlc-status` logic first and report where the pipeline currently stands.
3. Then execute the remaining steps **in order**, 1 through 8, using the same procedure as
   `/sdlc-step` for each one.
4. After every step: print the summary, ask
   `Approve step <N> and continue? (yes / changes needed)`, and **stop until answered**.
5. Never skip a step, never run two steps in one turn, never bypass a gate.
6. If any step's agent reports a blocker, stop the whole pipeline and report it.
7. Maintain a running progress table at the top of each response:
   `Step | Agent | Artifact | Status`.

Use `/compact` between steps if the context grows large, and keep the model on Sonnet.