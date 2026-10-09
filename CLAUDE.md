# CLAUDE.md — Repository Instructions

These rules apply to **every** session in this repository. They are not optional.

## What this repository is

Two layers:

| Layer | Content | Location |
|---|---|---|
| 1. Agentic SDLC pipeline | 8 SDLC subagents, 3 skills, slash commands, 2 enforcement hooks | `.claude/`, this file |
| 2. The product it delivers | `docsync` — a Python CLI that keeps docs in sync with the repo | `src/`, `tests/` |

The authoritative process definition is `.claude/AGENTIC_SDLC_PROCESS.md`.
The work item being delivered is `input/DS-1-user-story.md`.

## The 8-step pipeline and its artifacts

| Step | Agent | Artifact |
|---|---|---|
| 1 | requirements-analyst | `docs/01-requirements.md` |
| 2 | solution-architect | `docs/02-architecture.md` |
| 3 | design-reviewer | `docs/03-design-review.md` (+ may edit `02`) |
| 4 | impl-planner | `docs/04-impl-plan.md` |
| 5 | implementer | `src/`, `tests/` |
| 6 | code-reviewer | `docs/05-code-review.md` |
| 7 | verifier | `docs/06-verification.md`, `docs/PROJECT_DOCS.md` |
| 8 | pr-author | `docs/07-pr-description.md`, `CHANGELOG.md`, the PR |

## Golden rules

1. **Never skip a step.** Step N may only start when step N-1's artifact exists and the
   human has said "approved". If an upstream artifact is missing, stop and say so.
2. **Human gate.** At the end of every step, print a short summary and the exact question
   `Approve step <N> and continue? (yes / changes needed)`. Do not start the next step until
   the human answers.
3. **Never invent facts.** If a value cannot be derived from the repository, the user story,
   or a real command's output, write the literal string `Not Found`. Do not guess versions,
   counts, names, or test results.
4. **Traceability.** Every requirement gets an ID (`FR-1`, `NFR-1`). Architecture components,
   plan tasks, tests and review findings must reference those IDs.
5. **Evidence, not claims.** Any statement about tests, coverage or security must be backed by
   pasted output of a command you actually ran in this session.
6. **Secrets.** Never read, create or modify `.env`, `*.pem`, `*.key`, `secrets.*`,
   `credentials.*`. Never print an environment variable's value — only whether it is set.
   Only `.env.example` with empty placeholders may be written. A PreToolUse hook enforces this.
7. **Small, reviewable changes.** In step 5, implement **one task from `04-impl-plan.md` at a
   time**, then stop for approval. Never batch multiple tasks.
8. **One commit per step**, message format:
   `<type>(step-<N>): <summary>` where type is `docs`, `feat`, `test`, `chore`, or `refactor`.
   Include the artifact filenames in the commit body.
9. **Dates in artifacts must be derived from git commit metadata**, never assumed or supplied by the
   human. Use: `git log -1 --format=%cs <commit>`.

## Tech conventions for the product

- Python 3.11+, standard library first; only `requests` as a runtime dependency.
- `src/` layout, package `docsync`. Type hints on every public function.
- Tests: `pytest`, Arrange-Act-Assert, `tmp_path` / `monkeypatch`, no real network calls.
- Lint: `ruff check .` must be clean.
- No bare `except:`; raise/handle domain errors from `docsync/errors.py`.

## Definition of Done for any step

- [ ] Artifact written to the exact path in the table above
- [ ] All referenced requirement IDs exist in `docs/01-requirements.md`
- [ ] No secrets, no invented data, unknowns marked `Not Found`
- [ ] `ruff check .` and `pytest -q` clean (from step 5 onward)
- [ ] Changes staged and committed with the step-numbered message
- [ ] Human approval recorded in the chat