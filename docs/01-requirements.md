# Requirements — DS-1 Automated Documentation Sync

| Field | Value |
|---|---|
| Artifact | docs/01-requirements.md |
| SDLC Step | 1 — Requirements |
| Source documents | input/DS-1-user-story.md, CLAUDE.md, human clarification answers (chat) |
| Author | requirements-analyst |
| Date | 2026-10-07 |
| Status | Draft |

## 1. Scope

### In scope

| Item | Detail |
|---|---|
| CLI tool `docsync` | Subcommands `generate` and `check` |
| Output | A single Markdown file (default `docs/PROJECT_DOCS.md`) with exactly 7 sections |
| Data sources | Local repository files (e.g. `pyproject.toml`, source tree, tests) and the GitHub REST API |
| Drift detection | `docsync check` compares the committed document to a fresh generation |
| Platforms | GitHub only; Python projects only; one repository per run |

### Out of scope

| Item | Source |
|---|---|
| Publishing docs to a website | User story, Out of Scope |
| Non-Python projects | User story, Out of Scope; human answer Q15 |
| Editing or round-tripping hand-written prose | User story, Out of Scope |
| Platforms other than GitHub; multi-repo runs | Human answer Q15 |
| Volatile GitHub fields (stars, forks, open issues, last-push timestamp) | Human answer Q4 |
| Timestamps and commit hashes in the document | Human answer Q5 |

## 2. Glossary

| Term | Definition |
|---|---|
| in sync | The committed documentation file is byte-identical to a document freshly generated with the same configuration. Any difference is drift. |
| Not Found | The exact literal string `Not Found` (case and spacing exact), written in place of any value that cannot be determined. Never `N/A`, blank, or `unknown`. |
| offline mode | Operation with no network calls. Active when `--offline` is passed or when `DOCSYNC_GITHUB_TOKEN` is unset. All hosted-metadata fields render as `Not Found`. |
| drift | Any byte difference between the committed document and a fresh generation. |
| redaction | Replacement of secret-looking values by one shared function before any output is written or printed. |

## 3. Functional Requirements

| ID | Requirement | Source AC | Priority | Acceptance test |
|----|-------------|-----------|----------|-----------------|
| FR-1 | The system shall, on `docsync generate`, write a Markdown file to the path given by `--out`; when `--out` is not supplied the default is `docs/PROJECT_DOCS.md` under the `--repo` root, independent of the current working directory. | AC1 | Must | `tests/test_cli.py::test_generate_writes_default_output` (planned) |
| FR-2 | The system shall emit exactly 7 sections, in this order: Project Overview, Identity & Metadata, Hosted Repository Metadata, Modules & Entry Points, Dependencies, Test Suite Summary, Generation Info. | AC1 | Must | `tests/test_render.py::test_document_has_seven_sections_in_order` (planned) |
| FR-3 | The system shall render every value it cannot determine as the exact literal `Not Found`, and shall not blank or omit the field. | AC2 | Must | `tests/test_render.py::test_unresolved_fields_render_not_found` (planned) |
| FR-4 | The system shall include in Hosted Repository Metadata only these fields: `full_name`, `description`, `default_branch`, `visibility`, `license`, `topics`. | AC1, AC7 | Must | `tests/test_github.py::test_only_stable_fields_rendered` (planned) |
| FR-5 | The system shall limit Generation Info to the tool version and the document schema version, with no timestamp and no commit hash. | AC7 | Must | `tests/test_render.py::test_generation_info_has_no_volatile_values` (planned) |
| FR-6 | The system shall pass all text through one shared redaction function before it is written to a file or printed to the console. | AC3 | Must | `tests/test_redact.py::test_redaction_applied_to_file_and_console` (planned) |
| FR-7 | The system shall never read `.env` files. | AC3 | Must | `tests/test_collect.py::test_dotenv_never_opened` (planned) |
| FR-8 | The system shall read the API token only from the environment variable `DOCSYNC_GITHUB_TOKEN`, send it as a bearer token, and log only whether it is set or not set, never its value. | AC3 | Must | `tests/test_github.py::test_token_sent_as_bearer_and_never_logged` (planned) |
| FR-9 | The system shall run in offline mode when `DOCSYNC_GITHUB_TOKEN` is unset. | AC4 | Must | `tests/test_github.py::test_unset_token_means_offline` (planned) |
| FR-10 | The system shall make zero network calls when `--offline` is passed. | AC4 | Must | `tests/test_cli.py::test_offline_flag_makes_no_requests` (planned) |
| FR-11 | The system shall, on any API failure (timeout, 404, 403 rate limit, malformed JSON), log exactly one warning line to stderr, render every affected field as `Not Found`, continue, and exit 0. | AC4 | Must | `tests/test_github.py::test_api_failure_degrades_to_not_found` (planned) |
| FR-12 | The system shall use an HTTP timeout of 5 seconds and shall not retry failed requests. | AC4 | Must | `tests/test_github.py::test_timeout_is_5s_and_no_retry` (planned) |
| FR-13 | The system shall, on an empty repository, produce a complete document with all 7 sections, every unresolved field rendered as `Not Found`, and exit 0. | AC5 | Must | `tests/test_cli.py::test_empty_repo_produces_full_document` (planned) |
| FR-14 | The system shall render fields that depend on a missing `pyproject.toml` as `Not Found` and shall not crash. | AC5 | Must | `tests/test_collect.py::test_missing_pyproject` (planned) |
| FR-15 | The system shall, on `docsync check`, regenerate the document in memory using the same configuration and compare it byte-for-byte to the file at `--out`; it shall exit 0 if identical and 1 if different. | AC6 | Must | `tests/test_cli.py::test_check_in_sync_and_drift_exit_codes` (planned) |
| FR-16 | The system shall not modify any file during `docsync check`. | AC6 | Must | `tests/test_cli.py::test_check_does_not_write` (planned) |
| FR-17 | The system shall produce byte-identical output when `docsync generate` is run twice in succession on an unchanged repository (deterministic ordering, fixed line endings, no volatile values). | AC7 | Must | `tests/test_cli.py::test_generate_twice_is_byte_identical` (planned) |
| FR-18 | The system shall accept the flags `--repo PATH` (default `.`), `--out PATH` (default `<repo>/docs/PROJECT_DOCS.md`, resolved against the `--repo` root; an explicit relative `--out` is resolved against the current working directory and must end in `.md` and resolve inside `--repo`), `--github-repo OWNER/NAME` (optional), `--offline` and `--verbose` on both subcommands. | AC1 | Must | `tests/test_cli.py::test_flags_and_defaults` (planned) |
| FR-19 | The system shall exit 2 on invalid input or usage error and shall never display a Python traceback to the user. | AC4 | Must | `tests/test_cli.py::test_invalid_input_exit_2_no_traceback` (planned) |
| FR-20 | The system shall, when `--verbose` is set, print extra diagnostics to stderr, with the same redaction applied. | AC3 | Should | `tests/test_cli.py::test_verbose_output_is_redacted` (planned) |

## 4. Non-Functional Requirements

| ID | Requirement | Measurable target | Source | Verification |
|----|-------------|-------------------|--------|--------------|
| NFR-1 | Offline run time | Target: best of 3 measured in-process offline `generate` runs < 1.0 s wall-clock, after one discarded warm-up run, on the Q16 fixture (50 modules, 20 test files, 30 runtime + 5 optional dependencies, README.md, LICENSE). Test assertion (hard fail): best run < 2.0 s | Q10, Q16 | `tests/test_perf.py::test_offline_under_1s` (marker `perf`) |
| NFR-2 | Online run time | < 5 seconds, with 5-second HTTP timeout and no retries | Q10 | Mocked-timeout test plus verification step timing |
| NFR-3 | Test coverage | ≥ 85% line coverage on `src/docsync` | Q11 | `pytest --cov=src/docsync --cov-fail-under=85` |
| NFR-4 | Edge-case test traceability | 100% of EC-* items have at least one test whose name references the EC ID | Q11 | Review check in step 6 |
| NFR-5 | Runtime environment | Python 3.11+; standard library plus `requests` only; no other runtime dependency without human approval | Q13 | `pyproject.toml` inspection |
| NFR-6 | Lint cleanliness | `ruff check .` reports 0 findings | CLAUDE.md | `ruff check .` |
| NFR-7 | Test isolation | 0 real network calls in the test suite | CLAUDE.md | Tests use mocks / `monkeypatch` |
| NFR-8 | Determinism | 2 consecutive runs produce 0 differing bytes | AC7 | FR-17 test |
| NFR-9 | CI safety | No interactive prompts; exit codes limited to 0, 1, 2 | User story NFE, Q7 | `tests/test_cli.py` exit-code tests |
| NFR-10 | Secret hygiene | 0 occurrences of secret-looking values in generated document or console output across the test fixtures | AC3, Q12 | `tests/test_redact.py` |

## 5. Error and Edge Cases

| ID | Case | Required behaviour | Related FR |
|----|------|--------------------|------------|
| EC-1 | API timeout | One stderr warning; hosted fields `Not Found`; exit 0 | FR-11, FR-12 |
| EC-2 | API returns 404 | One stderr warning; hosted fields `Not Found`; exit 0 | FR-11 |
| EC-3 | API returns 403 rate limit | One stderr warning; hosted fields `Not Found`; exit 0 | FR-11 |
| EC-4 | API returns malformed JSON | One stderr warning; hosted fields `Not Found`; exit 0 | FR-11 |
| EC-5 | `DOCSYNC_GITHUB_TOKEN` unset | Offline mode; no network calls; hosted fields `Not Found` | FR-9 |
| EC-6 | Empty repository | Complete 7-section document; unresolved fields `Not Found`; exit 0 | FR-13 |
| EC-7 | Missing `pyproject.toml` | Dependent fields `Not Found`; no crash | FR-14 |
| EC-8 | Unreadable file | The affected field is `Not Found`; no crash; one warning line | FR-3, FR-19 |
| EC-9 | Secret-looking value in metadata | Value redacted by the shared function in file and console output | FR-6, NFR-10 |
| EC-10 | `--repo` path does not exist or is not a directory | Exit 2 with a one-line message; no traceback | FR-19 |
| EC-11 | `--github-repo` not in `OWNER/NAME` form | Exit 2 with a one-line message; no traceback | FR-19 |
| EC-12 | `check` run when the file at `--out` does not exist | Treated as drift: exit 1 (see A-4) | FR-15 |
| EC-13 | Malformed `pyproject.toml` | Dependent fields `Not Found`; one warning; no crash | FR-3, FR-19 |
| EC-14 | `--github-repo` omitted | Hosted fields `Not Found`; no network call (see A-2) | FR-3, FR-10 |

## 6. Clarifications Register

| Q | Question | Human answer | Resulting requirement ID |
|---|----------|--------------|--------------------------|
| Q1 | Which sections must the generated document contain? | Exactly 7: Project Overview, Identity & Metadata, Hosted Repository Metadata, Modules & Entry Points, Dependencies, Test Suite Summary, Generation Info. | FR-2 |
| Q2 | What does "in sync" mean precisely? | Committed file is byte-identical to a freshly generated document using the same configuration; any difference is drift. | FR-15, FR-17 |
| Q3 | How is the platform API authenticated? | Optional bearer token from env var `DOCSYNC_GITHUB_TOKEN` only; unauthenticated requests allowed; unset variable means offline mode. | FR-8, FR-9, EC-5 |
| Q4 | Which GitHub fields are included? | Only `full_name`, `description`, `default_branch`, `visibility`, `license`, `topics`. Volatile fields excluded for AC7. | FR-4 |
| Q5 | What goes in Generation Info? | Tool version and document schema version only; no timestamp, no commit hash. | FR-5 |
| Q6 | Exact CLI shape? | `docsync generate` and `docsync check`; flags `--repo PATH` (default `.`), `--out PATH` (default `docs/PROJECT_DOCS.md`, resolved against the `--repo` root since CR-4; see FR-1 and FR-18), `--github-repo OWNER/NAME` (optional), `--offline`, `--verbose`. | FR-1, FR-18 |
| Q7 | Exit codes? | 0 success / in sync; 1 drift detected by `check`; 2 invalid input or usage error; never leak a traceback. | FR-15, FR-19, NFR-9 |
| Q8 | Behaviour when the API fails? | One warning line to stderr, affected fields `Not Found`, continue, exit 0. | FR-11, EC-1..EC-4 |
| Q9 | Behaviour on an empty repository? | Complete valid document with all 7 sections, unresolved fields `Not Found`, exit 0. | FR-13, EC-6 |
| Q10 | Performance target? | Offline < 1 s; online < 5 s; 5 s HTTP timeout; no retries. | NFR-1, NFR-2, FR-12 |
| Q11 | Test coverage target? | ≥ 85% line coverage on `src/docsync`; every EC-* has a named test. | NFR-3, NFR-4 |
| Q12 | Secret handling? | One shared redaction function before anything is written or printed; `.env` never read; only set/not set logged about a token. | FR-6, FR-7, FR-8, NFR-10 |
| Q13 | Supported Python / dependencies? | Python 3.11+; standard library plus `requests`; no new runtime dependency without approval. | NFR-5 |
| Q14 | "Not Found" exact spelling? | The literal string `Not Found`, not `N/A`, not blank, not `unknown`. | FR-3 |
| Q15 | Which platforms / project types? | GitHub only; Python projects only; single repository per run. | Scope, EC-14 |
| Q16 | Which repository does the NFR-1 offline performance measurement use, and how is it measured? (decision RO-1, given at the step 5 T17 gate) | Fixture built in a temporary directory, offline only, no network, no subprocess: 50 Python modules (5 packages x 10 modules, about 10 lines each); 20 test files with 2 test functions each; a `pyproject.toml` declaring 30 runtime dependencies and 5 optional dependencies; a README.md and a LICENSE file. Method: call the generate path in-process (no subprocess, to exclude interpreter startup); one discarded warm-up call; then 3 measured calls with `time.perf_counter`; the best (minimum) duration counts; offline forced explicitly (token unset and `--offline`). Budget: target best run < 1.0 s; the test fails the build only if the best run is >= 2.0 s, so an order-of-magnitude regression is caught without CI jitter causing false failures. The test prints the measured best duration. | NFR-1 |

## 7. Assumptions

| ID | Assumption | Status |
|----|-----------|--------|
| A-1 | The exact content of each non-GitHub section (e.g. which `pyproject.toml` keys feed Identity & Metadata, whether Test Suite Summary is derived statically from test files rather than by running tests) was not specified by the human. This is deferred to step 2 (architecture) and must be derived only from repository files. | Open — confirm at step 2 gate |
| A-2 | Without `--github-repo`, the tool does not try to infer the repository from git remotes; hosted fields are `Not Found`. | Open — not stated by human |
| A-3 | The repository size used for the NFR-1 performance measurement was not specified at step 1. | Resolved by the human as decision RO-1: see Q16 and NFR-1 |
| A-4 | `check` treats a missing committed document as drift (exit 1), since the committed file is not byte-identical to a fresh generation. | Derived from the definition of "in sync" |
| A-5 | A token being set while `--offline` is passed still results in no network calls; `--offline` wins. | Derived from FR-10 |
| A-6 | The `check` command uses the same flags (`--offline`, `--github-repo`) as `generate`, so "same configuration" is reproducible. | Derived from Q2 and Q6 |
| A-7 | The schema version value and tool version value are defined at implementation time and not invented here. | Not Found |

## 8. Traceability

| User-story AC | Description | FR / NFR IDs | Gap? |
|---|---|---|---|
| AC1 | Tool produces a Markdown documentation file | FR-1, FR-2, FR-4, FR-18 | No |
| AC2 | Undeterminable info shown as `Not Found` | FR-3, EC-7, EC-8, EC-13, EC-14 | No |
| AC3 | Secrets never in document or console output | FR-6, FR-7, FR-8, FR-20, NFR-10, EC-9 | No |
| AC4 | API unreachable, slow, or erroring still gives a usable document | FR-9, FR-10, FR-11, FR-12, FR-19, EC-1..EC-5 | No |
| AC5 | Works on empty or brand-new repository | FR-13, FR-14, EC-6, EC-7 | No |
| AC6 | Reviewers can tell whether docs are in sync | FR-15, FR-16, EC-12 | No |
| AC7 | Two runs in a row do not change the doc | FR-5, FR-17, NFR-8, FR-4 | No |

Non-functional expectations from the story map as follows: "fast" → NFR-1, NFR-2; "safe in CI" → NFR-9; "well tested" → NFR-3, NFR-4, NFR-7; "easy to run" → FR-18 (defaults for all flags).

---
**Gate:** Approve step 1 and continue? (yes / changes needed)
