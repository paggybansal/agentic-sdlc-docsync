---
description: Run one SDLC step for DS-1 and stop at its human approval gate. Usage - /sdlc-step 3
argument-hint: <step-number 1-8>
---

Run SDLC step **$1** for work item DS-1.

## Procedure

1. Read `CLAUDE.md` and `.claude/AGENTIC_SDLC_PROCESS.md`.
2. Read the agent file for step $1 from `.claude/agents/` (file name starts with `$1-`).
   That file is your binding role contract for this step.
3. **Gate check:** confirm the artifact of step $1 minus 1 exists. If it does not, stop and
   report which step must run first. Do not proceed.
4. **Choose execution mode** from the agent file's `Execution mode`:
   - *main thread* (steps 1, 5, 8): adopt the agent's role yourself in this conversation so you
     can ask the human questions and wait for answers.
   - *delegated subagent* (steps 2, 3, 4, 6, 7): invoke that subagent with the Task tool,
     passing the paths of its input documents, then review what it produced before showing it.
5. Load the skills the agent file names.
6. Produce the artifact exactly as the agent's **Output contract** specifies.
7. Print:
   - a 5-line summary of what was produced
   - the "Done when" checklist with each item ticked or explained
   - any unknown values you recorded as `Not Found`
8. Ask: `Approve step $1 and continue? (yes / changes needed)` and **stop**.
9. Only after the human says yes, stage and commit with the message format from `CLAUDE.md`.

## Prohibitions

- Do not start step $1 plus 1 in this command.
- Do not invent test results, coverage numbers or metadata.
- Do not write to any path blocked by the `block_secrets` hook.