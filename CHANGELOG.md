# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Repository scaffold for the Agentic SDLC capstone (DS-1).
- `docsync` CLI with two commands, `generate` and `check` (DS-1). `generate` writes a seven-section `docs/PROJECT_DOCS.md`; `check` compares bytes, never writes, and exits 0 (in sync), 1 (drift) or 2 (invalid input or error).
- Offline-first collector: reads `pyproject.toml` and scans the repository's modules and tests statically; hosted GitHub metadata is requested only when `--github-repo` is given and `DOCSYNC_GITHUB_TOKEN` is set, and every failure degrades to a one-line warning and `Not Found` (DS-1).
- Secret redactor (`src/docsync/redact.py`) with bounded-time patterns for literal secrets, prefixed credentials, headers, URL userinfo and key-value pairs (DS-1).
- Deterministic renderer: LF line endings, one trailing newline, no timestamps or hashes, so repeated runs are byte-identical (DS-1).
- Agentic SDLC pipeline under `.claude/`: eight subagents, three skills, three slash commands (`/sdlc-step`, `/sdlc-status`, `/sdlc-run`) and two enforcement hooks (`block_secrets.py`, `run_tests.py`), governed by `CLAUDE.md`.
- CI workflow (`.github/workflows/ci.yml`): lint and tests with coverage on ubuntu-latest and windows-latest (Python 3.11 and 3.12), an advisory `pip-audit` job, and a self-enforcing documentation sync gate (`docsync generate` then `docsync check` against the committed `docs/PROJECT_DOCS.md`).
- MIT `LICENSE`, the committed offline rendering `docs/PROJECT_DOCS.md`, and SDLC artifacts `docs/01-requirements.md` to `docs/07-pr-description.md`.

### Changed
- The default `--out` now resolves against the `--repo` root instead of the current working directory (CR-4).

### Fixed
- CR-1: ReDoS in the redactor; every pattern now has bounded quantifiers.
- CR-2: secret shapes that were not redacted (`sk-`, `AKIA`, `xox`, JWT, PEM blocks, URL userinfo) are now covered.
- CR-33: prefixed credentials are redacted without requiring mixed case or a digit.

### Security
- Redaction is applied at a single CLI choke point: every console message goes through `_emit` and the document through `redact` before any write or print.
- Configuration is read only from environment variables (`DOCSYNC_GITHUB_TOKEN`); the tool never reads `.env`, and the token's value is never printed (only whether it is set).

### Removed
- The empty `src/docsync/collectors/` stub package (RO-2, DS-1).
