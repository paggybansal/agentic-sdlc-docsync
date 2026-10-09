# Agentic SDLC Process

End-to-end, agent-driven software delivery lifecycle implemented with Claude Code.
Demonstrated by delivering one real work item: **DS-1 — Automated Documentation Sync**.

## Pipeline
input/DS-1-user-story.md
│
▼
[1] requirements-analyst ──► docs/01-requirements.md (human Q&A)
▼
[2] solution-architect ──► docs/02-architecture.md
▼
[3] design-reviewer ──► docs/03-design-review.md ──┐
▼ └─► updates 02
[4] impl-planner ──► docs/04-impl-plan.md
▼
[5] implementer ──► src/ + tests/ (task-by-task approval)
│ ▲
│ └── hook: run_tests.py (pytest after every edit)
▼
[6] code-reviewer ──► docs/05-code-review.md
▼
[7] verifier ──► docs/06-verification.md + docs/PROJECT_DOCS.md
▼
[8] pr-author ──► docs/07-pr-description.md + CHANGELOG.md + Pull Request


## Primitives used

| Primitive | Where | Purpose |
|---|---|---|
| **Instructions** | `CLAUDE.md` | Always-on rules: gates, traceability, secrets policy, commit format |
| **Agents** | `.claude/agents/*.md` | One specialised role per SDLC step, with its own tool allow-list |
| **Skills** | `.claude/skills/*/SKILL.md` | Reusable know-how: doc templates, test standards, secret safety |
| **Prompts / commands** | `.claude/commands/*.md` | `/sdlc-step`, `/sdlc-status`, `/sdlc-run` |
| **Hooks** | `.claude/settings.json` + `.claude/hooks/*.py` | Deterministic enforcement that does not depend on the model's goodwill |

## Hooks

| Hook | Event | Effect |
|---|---|---|
| `block_secrets.py` | `PreToolUse` on Write/Edit | Exit 2 → **denies** writes to `.env`, `*.pem`, `*.key`, `secrets.*`, `credentials.*` |
| `run_tests.py` | `PostToolUse` on Write/Edit | Runs `pytest -q` after any `src/` or `tests/` change; failures are fed back to the agent automatically |

## Execution model

Subagents cannot pause to ask the user. Steps that require human dialogue (1, 5, 8) are
therefore executed in the main thread using the agent file as the role contract; steps
2, 3, 4, 6, 7 are delegated to subagents. See each agent file's **Execution mode**.

## Human gates

Eight gates, one per step. The pipeline halts after each artifact and asks
`Approve step <N> and continue? (yes / changes needed)`.

## Usage
/sdlc-status # what is done, what is next
/sdlc-step 1 # run one step, then stop at its gate
/sdlc-run # orchestrate all steps, halting at every gate


## Evidence

Screenshots and command transcripts per step are stored in `evidence/`.