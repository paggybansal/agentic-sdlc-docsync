---
description: Show which SDLC artifacts exist, which step is next, and whether the repo is clean.
---

Report the current state of the Agentic SDLC pipeline for DS-1.

1. For each row below, check whether the file exists and report `DONE` or `PENDING`:
   - 1 Requirements -> `docs/01-requirements.md`
   - 2 Architecture -> `docs/02-architecture.md`
   - 3 Design Review -> `docs/03-design-review.md`
   - 4 Impl Plan -> `docs/04-impl-plan.md`
   - 5 Implementation -> any file under `src/docsync/` besides `__init__.py`
   - 6 Code Review -> `docs/05-code-review.md`
   - 7 Verification -> `docs/06-verification.md`
   - 8 Pull Request -> `docs/07-pr-description.md`
2. Run `git status --short` and `git log --oneline -10`.
3. Print a table: `Step | Artifact | Status | Commit`.
4. State the next step to run and the exact command: `/sdlc-step <N>`.
5. Do not modify any file in this command.