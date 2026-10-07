# agentic-sdlc-docsync

An **Agentic SDLC pipeline** built with Claude Code, demonstrated end-to-end by delivering
one real feature: **`docsync`**, a CLI that keeps project documentation in sync with the
repository and its GitHub metadata.

## Two layers of this project

| Layer | What | Where |
|---|---|---|
| 1. The pipeline | 8 SDLC subagents, 3 skills, repo instructions, slash commands, 2 hooks | `.claude/`, `CLAUDE.md` |
| 2. The product | `docsync` CLI + pytest suite, delivered *by* the pipeline | `src/`, `tests/` |

## SDLC artifacts

| Step | Artifact |
|---|---|
| Input | `input/DS-1-user-story.md` |
| 1. Requirements | `docs/01-requirements.md` |
| 2. Architecture | `docs/02-architecture.md` |
| 3. Design Review | `docs/03-design-review.md` |
| 4. Implementation Plan | `docs/04-impl-plan.md` |
| 5. Implementation | `src/`, `tests/` |
| 6. Code Review | `docs/05-code-review.md` |
| 7. Verification | `docs/06-verification.md` |
| 8. Pull Request | `docs/07-pr-description.md` |
| Tool output | `docs/PROJECT_DOCS.md` |

## Quick start

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
pytest -v


---

### 📄 `.github/pull_request_template.md`

```markdown
## Summary
<!-- 2-3 sentences: what was built and why -->

## Changes Made
<!-- Bulleted list: every file added/modified + the reason -->

## Test Evidence
<!-- Paste test run output and/or link to CI results -->

## Known Limitations
<!-- Anything rendered as "Not Found", deferred, or out of scope -->

## Reviewer Checklist
- [ ] Behaviour matches `docs/01-requirements.md`
- [ ] No secrets in code, logs, or generated output
- [ ] User input is validated
- [ ] API failures / missing files / empty repo handled gracefully
- [ ] Tests cover happy path **and** "Not Found" / missing-field cases
- [ ] Function names are self-explanatory; logic readable without comments
- [ ] No duplicated logic that should be shared
- [ ] No known-vulnerable dependency versions (`pip-audit` clean)