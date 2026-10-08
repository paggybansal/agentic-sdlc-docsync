# Implementation Plan — DS-1 Automated Documentation Sync

| Field | Value |
|---|---|
| Artifact | docs/04-impl-plan.md |
| SDLC Step | 4 — Implementation Plan |
| Source documents | docs/01-requirements.md, docs/02-architecture.md (v1.1), docs/03-design-review.md (outcome: Approved with conditions), CLAUDE.md |
| Author | impl-planner |
| Date | 2026-10-07 |
| Status | Draft |

## 1. Plan Summary

| Item | Value |
|---|---|
| Task count | 22 (T1 to T19 plus T13b, added at the T13 gate, T20, added after the step 6 review, and T21, the final remediation round); 20 production-code tasks, T18 and T19 are verification tasks |
| Size rule | Each production task is at most ~40 lines of production code; its tests are part of the same task (Done criteria) |
| Total estimate | 580 minutes if done sequentially by one implementer (560 plus 20 for T13b; T20 and T21 were not estimated by the human, so their estimates are `Not Found`); critical path 280 minutes (Section 5) |
| Step 5 rule | One task at a time, stop for human approval after each (CLAUDE.md rule 7) |

Build order rationale (matches the mandated order): errors/model/sentinel (T1) -> redactor (T3, T4) and collectors (T5 to T7, T8 to T10) -> renderer (T11, T12) -> CLI (T13 to T15) -> `check` mode (T16, only after `generate` works end to end in T14/T15) -> integration, perf and quality gates (T17 to T19). Redaction is built early because the CLI (T13) echoes user input through it (ADD-1). `.gitattributes` (T2) has no code dependency and satisfies the step 3 condition for ADD-4.

Binding step 3 conditions and where they land:

| Condition | Where |
|---|---|
| `.gitattributes` LF entry (ADD-4, DR-3) | T2 |
| Perf fixture size for NFR-1 (A-3, DR-12) | Resolved by the human as RO-1 (Section 9); implemented in T18 |
| Tests for each redaction pattern, empty token, RequestException subclasses, partial payloads, `check` read-error exit 2, KeyboardInterrupt/BrokenPipeError exit 2 | T4 (patterns, empty token), T9 (RequestException subclasses), T10 (partial payloads), T15 (interrupt/pipe), T16 (check read error); see Section 6 |

Assumptions:

| ID | Assumption |
|---|---|
| PA-1 | `src/docsync/__init__.py` already defines `__version__ = "0.1.0"` and `pyproject.toml` already declares `docsync.cli:main`, `requests>=2.32.0`, pytest/ruff config and coverage config (read from the repository). T1 and T11 reuse them and do not change the version. |
| PA-2 | A stub `src/docsync/collectors/__init__.py` already exists but the architecture (C-4) specifies a single `collect.py`. The plan builds `collect.py` and leaves the stub untouched; whether to remove it is Not Found (needs human decision, see Section 8). |
| PA-3 | Document schema version (A-7, OQ-4): T1 defines `SCHEMA_VERSION = "1"` as a plan-level decision, to be confirmed by the human at the step 4 gate. Tool version comes from `docsync.__version__`. |
| PA-4 | Perf fixture size for NFR-1: fixed by the human as decision RO-1 (Section 9); no longer `Not Found`. The implementer must not change it. |
| PA-5 | Test code is not counted toward the ~40-line production limit; test files are listed in Files touched. |
| PA-6 | Estimates are planning estimates for one implementer including tests; they are not measured data. |
| PA-7 | Each EC test name contains its EC id (NFR-4), e.g. `test_ec_2_api_404_degrades`. |

## 2. Task Table

| ID | Task | Files touched | Satisfies (FR/EC/ADD IDs) | Blocked by | Est. (min) | Done criteria |
|---|---|---|---|---|---|---|
| T1 | Domain errors, `NOT_FOUND` sentinel, `FieldValue`, frozen `ProjectFacts`, `SCHEMA_VERSION`; add autouse no-network fixture in `tests/conftest.py` | `src/docsync/errors.py`, `src/docsync/model.py`, `tests/conftest.py`, `tests/test_model.py` | FR-3, FR-13, FR-19, ADD-7, NFR-7 | none | 25 | `NOT_FOUND == "Not Found"` exactly; `DocsyncError`, `UsageError`, `CollectError`, `GitHubError` exist with base class; `ProjectFacts` is frozen and has no timestamp/hash field; no `Field` class (ADD-7); autouse fixture makes `requests.Session.request` raise; `pytest -q` and `ruff check .` clean |
| T2 | Add `.gitattributes` with `docs/PROJECT_DOCS.md text eol=lf` | `.gitattributes` | ADD-4, ADD-3, FR-17 | none | 10 | File exists at repo root and contains exactly that rule; `git check-attr eol docs/PROJECT_DOCS.md` output pasted showing `eol: lf`; no other file touched |
| T3 | `redact(text, secrets=())` core: literal secrets (longest first, empty/whitespace ignored), token prefixes `ghp_ gho_ ghu_ ghs_ ghr_ github_pat_`, placeholder `[REDACTED]` | `src/docsync/redact.py`, `tests/test_redact.py` | FR-6, EC-9, NFR-10, ADD-1 | T1 | 25 | Pure function, reads no environment (DR-2); tests: one test per prefix (6), literal secret replaced, longest-first ordering, empty-token and whitespace-token cases leave text unchanged (DR-1); `ruff` clean |
| T4 | Extend `redact`: `Authorization:` header values, `Bearer <value>`, URL userinfo `scheme://user:pass@host`, `key=value`/`key: value` with token/secret/password/passwd/key/credential; fix pattern order; idempotency | `src/docsync/redact.py`, `tests/test_redact.py` | FR-6, FR-20, EC-9, NFR-10, ADD-1 | T3 | 35 | One test per pattern (header, Bearer, URL userinfo, key=value for each of the 6 key words); `redact(redact(x)) == redact(x)` test; same input gives same output; pattern order matches architecture Section 7; `test_redaction_applied_to_file_and_console` is deferred to T14 (needs CLI) |
| T5 | `collect.py` part 1: read `pyproject.toml` via `tomllib` into overview, identity (`version`, `requires_python`, `license`, `authors` names, declaration order), dependencies, optional dependencies, entry points; missing and malformed handling | `src/docsync/collect.py`, `tests/test_collect.py` | FR-3, FR-7, FR-14, EC-7, EC-8, EC-13, ADD-3, ADD-8 | T1 | 35 | Missing file gives `Not Found` fields, no warning (EC-7); `TOMLDecodeError` gives `Not Found` plus one warning (EC-13); unreadable file (`OSError`/`UnicodeDecodeError`) gives one warning (EC-8); dependencies and optional groups sorted by code point; only `pyproject.toml` opened; `ruff` clean |
| T6 | `collect.py` part 2: module scan, relative POSIX paths, Section 11 skip list, no symlinked dirs, `src/` preferred else repo root | `src/docsync/collect.py`, `tests/test_collect.py` | FR-3, EC-6, EC-8, ADD-3, ADD-8 | T5 | 30 | Tests with `tmp_path`: skip list names (`.git`, `tests`, `venv`, `build`, `node_modules`, `*.egg-info`, etc.) excluded; symlinked dir not followed; output sorted by code point; empty repo gives empty tuple; `src/` used when present |
| T7 | `collect.py` part 3: static test summary via `ast` (files and `test_*` functions incl. class methods, async), `SyntaxError` file counted plus one warning; public `collect(repo) -> (facts_parts, warnings)` assembling all-default facts for an empty repo | `src/docsync/collect.py`, `tests/test_collect.py` | FR-3, FR-7, FR-13, EC-6, EC-8, ADD-8 | T6 | 35 | Counts correct for module-level, method, async cases; `SyntaxError` file counted as a file with 0 functions and one warning; `test_dotenv_never_opened` patches `open`/`Path.read_text` and asserts `.env` never touched (FR-7); `test_ec_6_empty_repo` returns complete default facts |
| T8 | `github.py` part 1: `fetch(github_repo, offline, token, session)` decision logic only; offline when `--offline`, token unset, or repo omitted; all six hosted keys `Not Found` | `src/docsync/github.py`, `tests/test_github.py` (with `FakeSession`) | FR-9, FR-10, EC-5, EC-14, ADD-2 | T1 | 25 | Zero `session.get` calls in the three offline conditions; `--offline` wins even if token set (A-5); hosted dict has exactly the six FR-4 keys; empty/whitespace token treated as unset (DR-1/DR-2 alignment); `FakeSession` helper defined (about 15 lines, test code) |
| T9 | `github.py` part 2: single GET to hard-coded `https://api.github.com/repos/{owner}/{name}`, `Authorization: Bearer`, `timeout=5`, no retry; catch `requests.RequestException`, non-2xx, `ValueError`, non-dict payload; one fixed-text warning, no exception text echoed | `src/docsync/github.py`, `tests/test_github.py` | FR-8, FR-11, FR-12, EC-1, EC-2, EC-3, EC-4, ADD-2, ADD-5 | T8 | 35 | Tests: exactly one call, `timeout == 5`, bearer header present, URL host fixed; `Timeout`, `ConnectionError`, `SSLError`, `TooManyRedirects` each give one warning and six `Not Found` (RequestException subclasses, condition 3); 404 (EC-2), 403 (EC-3), invalid JSON (EC-4), JSON list payload each one warning; token value never in warning text or logs (set/not set only); mocked-timeout test supports NFR-2 |
| T10 | `github.py` part 3: per-field extraction of the six fields; `license` from nested object, `topics` sorted by code point; individual missing/null/empty/wrong-type field gives only that field `Not Found`, no warning | `src/docsync/github.py`, `tests/test_github.py` | FR-3, FR-4, EC-4, ADD-3, ADD-5 | T9 | 30 | Tests: full valid payload gives six fields; `license: null`, missing keys, empty topics, wrong types give per-field `Not Found` with zero warnings (partial payloads, condition 3); topics returned sorted; extra API fields (stars, forks, pushed_at) never appear |
| T11 | `render.py` part 1: normalisation helper (CR/LF to space, whitespace collapse, `\|` escape), section 1 Overview, 2 Identity, 3 Hosted, 7 Generation Info (`__version__`, `SCHEMA_VERSION` only) | `src/docsync/render.py`, `tests/test_render.py` | FR-2, FR-3, FR-5, ADD-3 | T1 | 35 | Fed hand-built `ProjectFacts`; `Not Found` rendered for sentinel; newline/CR/pipe in a description cannot alter structure; Generation Info has no timestamp or hash (`test_generation_info_has_no_volatile_values`); `ruff` clean |
| T12 | `render.py` part 2: sections 4 Modules & Entry Points, 5 Dependencies, 6 Test Suite Summary; `render(facts)` emits exactly 7 sections in order, LF, exactly one trailing `\n`; empty collections render `Not Found` | `src/docsync/render.py`, `tests/test_render.py` | FR-2, FR-3, FR-13, FR-17, EC-6, ADD-3 | T11 | 35 | `test_document_has_seven_sections_in_order`; `test_unresolved_fields_render_not_found`; all-default facts render a full 7-section document (EC-6); no `\r` in output; render called twice gives identical string |
| T13 | `cli.py` part 1: argparse with `generate`/`check` subparsers and flags `--repo --out --github-repo --offline --verbose`; `error()` override exits 2; validation of `--repo` (EC-10) and `--github-repo` strict pattern with `.`/`..` rejected (EC-11); `UsageError` messages passed through `redact` | `src/docsync/cli.py`, `tests/test_cli.py` | FR-18, FR-19, EC-10, EC-11, ADD-1, ADD-2 | T1, T4 | 30 | `test_flags_and_defaults`; missing subcommand gives exit 2; non-existent `--repo` and file-as-`--repo` give one-line message, exit 2, no traceback (EC-10); `a`, `a/b/c`, `../x`, `./.`, `o/..` and query characters rejected (EC-11); `--help` works |
| T13b | `cli.py` part 1b: `--out` safety validation inside `parse_args` (`UsageError`, exit 2, message through `redact`): (i) `--out` must end in `.md`; (ii) the resolved `--out` must lie inside the resolved `--repo`, which is the repository root for this rule. A relative `--out` still resolves against the current working directory (ADD-9) and is then checked against `--repo`. Execution order: after T14 (human decision at the T13 gate that T14 starts first); T15 is blocked by T13b | `src/docsync/cli.py`, `tests/test_cli.py` | FR-18, FR-19, ADD-9 (amended); the `.md` and containment rules were decided by the human at the T13 gate and have no earlier requirement or ADD ID (`Not Found`) | T13 | 20 | Tests: `.md` accepted and `.txt`, no suffix, `.markdown` rejected (case of `.MD` is an implementer default, case-insensitive, to confirm at the gate); `../x.md`, an absolute path outside `--repo`, and a `..` escape after a subdirectory rejected; an absolute path inside `--repo` accepted; the default `docs/PROJECT_DOCS.md` accepted when the cwd is `--repo`; both paths compared after `resolve()`; every rejection is one line, exit 2, no traceback, echoed input only via `redact`; `ruff` clean **Superseded for the default by CR-4 (RO-3):** the default `--out` is now `<repo>/docs/PROJECT_DOCS.md`, resolved against the `--repo` root and independent of the cwd; only an explicitly supplied relative `--out` resolves against the cwd |
| T14 | `cli.py` part 2: `generate` orchestration (collect, token from `DOCSYNC_GITHUB_TOKEN` passed on, fetch, build facts, render, `redact(text, secrets=(token,))`, byte-mode write with parent dirs, stdout `wrote <path>`, warnings to stderr, `--verbose` diagnostics redacted, only set/not set logged) | `src/docsync/cli.py`, `tests/test_cli.py` | FR-1, FR-6, FR-8, FR-10, FR-13, FR-20, ADD-1, ADD-9 | T4, T7, T10, T12, T13 | 40 | `test_generate_writes_default_output`; `test_offline_flag_makes_no_requests`; `test_redaction_applied_to_file_and_console` (secret in pyproject description absent from file and capsys); `test_verbose_output_is_redacted`; token value never in stdout/stderr (only set/not set); written bytes are LF, UTF-8, relative `--out` resolved against cwd (ADD-9) |
| T15 | `cli.py` part 3: top-level handler in `main`: `DocsyncError`, `OSError`, `KeyboardInterrupt`, `BrokenPipeError`, final `except Exception` all map to exit 2 with one-line message and no traceback; add `__main__.py` | `src/docsync/cli.py`, `src/docsync/__main__.py`, `tests/test_cli.py` | FR-19, NFR-9, ADD-6 | T14, T13b | 30 | `test_invalid_input_exit_2_no_traceback`; injected `KeyboardInterrupt` and `BrokenPipeError` each return exit 2 with no traceback in output; write failure at `--out` (for example `--out` is a directory) gives exit 2; generic exception shows type name only under `--verbose`; `python -m docsync --help` runs (output pasted); no bare `except:` |
| T16 | `cli.py` part 4: `check` mode: regenerate in memory with same config, compare bytes to `--out`, exit 0 identical, 1 drift; only `FileNotFoundError` is drift; other read `OSError` exit 2; never writes; drift hint line | `src/docsync/cli.py`, `tests/test_cli.py` | FR-15, FR-16, EC-12, ADD-6, ADD-10 | T15 | 30 | `test_check_in_sync_and_drift_exit_codes`; `test_ec_12_check_missing_file_is_drift` exit 1; `test_check_read_error_exit_2` (`--out` is a directory) exit 2, not 1 (condition 3); `test_check_does_not_write` (file mtime/bytes and directory listing unchanged); stdout is `drift detected: run "docsync generate" to update <path>` and no diff; no NotImplementedError remains anywhere in src/ (exit condition for step 5: `git grep -n NotImplementedError -- src` returns nothing) |
| T17 | Integration tests only (no production code): double-run determinism, empty repo end to end, Windows-style/CRLF description input, check after generate, full sections on a realistic fixture | `tests/test_cli.py`, `tests/test_integration.py` | FR-13, FR-17, NFR-8, EC-6, ADD-3 | T16 | 35 | `test_generate_twice_is_byte_identical` (0 differing bytes); `test_empty_repo_produces_full_document`; generate then check returns 0; no absolute paths or `\\` separators in output; failures here that point to production code are fixed in the owning task's files, not by new features |
| T18 | Add `test_offline_under_1s` to the RO-1 specification (Section 9) and register the `perf` pytest marker | `tests/test_perf.py`, `pyproject.toml` (marker registration only; added at the T17 gate) | NFR-1, FR-10 | T16 | 20 | Fixture and method exactly as RO-1; `@pytest.mark.perf` registered in `[tool.pytest.ini_options] markers`; in-process generate, one discarded warm-up, 3 measured runs, best (minimum) by `time.perf_counter`; offline forced (token unset and `--offline`); no network and no subprocess; asserts best run < 2.0 s and prints the measured best duration against the 1.0 s target; `ruff check .` clean; full suite green |
| T19 | Quality gates and verification inputs: run `ruff check .`, `pytest -q`, `pytest --cov=src/docsync --cov-fail-under=85`, confirm NFR-4 EC-to-test naming and NFR-5 dependencies | none (fixes land in owning task files) | NFR-3, NFR-4, NFR-5, NFR-6, NFR-7, NFR-9 | T2, T17, T18 | 20 | Pasted command output: ruff 0 findings; all tests pass; coverage >= 85%; every EC-1..EC-14 has at least one test name containing its id (grep output pasted); `pyproject.toml` runtime dependencies are only `requests`; exit codes only 0/1/2 asserted by tests |
| T20 | Harden the redactor (fixes CR-1, CR-2 and CR-3 from `docs/05-code-review.md`). Every regex quantifier explicitly bounded (no open-ended `+`, `*` or `{n,}`), no nested or ambiguous quantifiers, all patterns compiled once at import into a module-level tuple. Full pattern set of the secret-safety skill: `sk-` keys, `ghp_`, `github_pat_`, other `gh[pousr]_` tokens, AWS `AKIA` key ids, Slack `xox[baprs]-`, JWT `eyJ...`, PEM private-key header and body, and a bounded base64 blob redacted only if it contains an uppercase letter, a lowercase letter and a digit. The key=value rule is rewritten (CR-3). `cli.py` stays the single redaction choke point and `render.py` must not call the redactor | `src/docsync/redact.py`, `tests/test_redact.py`, `tests/test_integration.py` (the end-to-end choke-point test only) | CR-1, CR-2, CR-3, FR-6, FR-20, EC-9, NFR-10, ADD-1 | T4, T19 | Not Found | Tests: (a) one positive test per pattern class; (b) a ReDoS regression test on pathological 20,000-character inputs, each call under 1.0 s by `time.perf_counter`, marked `@pytest.mark.perf`; (c) false-positive tests that must NOT be redacted: a long dependency-list line, a 64-character SHA-256 hex string, a long lowercase-only string, a long module path, a normal sentence, `keygen = 1`, `keyring=abc`, `API key: rotate it`, `key = value`; (d) must be redacted: a genuine mixed-case base64 blob, `api_key=ghp_<token>`, a token-shaped assignment of 20+ characters; (e) idempotency: redacting redacted text is a no-op; (f) a structural test that every quantifier in every compiled pattern is bounded; (g) an end-to-end test: a fixture repo whose pyproject description contains token-shaped strings, run generate, assert on the file bytes on disk and on captured stdout and stderr, not on an internal call; (h) a source test that only `cli.py` imports the redactor. `ruff check .` clean, full suite green, hook passes |
| T21 | FINAL remediation round for step 6, in three parts. **T21a (code):** harden `redact.py` against false negatives and false positives. CR-17: add the missing key shapes (quoted keys such as `{"password": "x"}`, plural and suffixed keys such as `passwords=` and `SECRET_KEY=`, key and value in separate Markdown table cells), every new pattern bounded and compiled at module level; CR-19: stop mangling non-secret structured text (GitHub URLs, repository full names, topics, licence identifiers, ordinary paths, long camel-case identifiers, `sk-` package names); CR-22: apply the fix or the wording change and state which. **T21b (documentation truth alignment):** fix only statements where a document contradicts the implemented code: CR-23 (docs/02 section 7), CR-24 (the secret-safety skill pattern list and verification line), CR-25 (the residual pre-CR-4 default statements); anything merely incomplete is not fixed and is listed as not fixed with the reason. **T21c (date integrity):** dates in artifacts are derived from `git log -1 --format=%cs <commit>`; correct the dates in docs/05-code-review.md section 8; the CLAUDE.md golden rule 9 was committed separately (`4bd4fb8`) | `src/docsync/redact.py`, `tests/test_redact.py` (T21a); `docs/02-architecture.md`, `docs/01-requirements.md`, `docs/04-impl-plan.md`, `.claude/skills/secret-safety/SKILL.md`, `docs/05-code-review.md` (T21b, T21c) | CR-17, CR-19, CR-22, CR-23, CR-24, CR-25, FR-6, FR-20, EC-9, NFR-10 | T20 | Not Found | T21a tests: one positive test per new key shape; byte-identical survival of `https://github.com/parag-bansal/agentic-sdlc-docsync`, `https://api.github.com/repos/octocat/Hello-World`, `octocat/Hello-World`, `MIT`, `Apache-2.0` and `src/docsync/collectors/github_api.py`, plus every other mangled shape found; the ReDoS regression test re-run with the measured duration reported again; exactly one redaction function, no unbounded quantifier (structural test), `render.py` does not import the redactor. T21b: for each correction the document, the false claim and the correction are stated. T21c: section 8 dates equal the git commit dates. `ruff check .` clean, full suite green, hook passes. **Remediation freeze applies (RO-4)** |

Requirement coverage check. FR-1 T14; FR-2 T11, T12; FR-3 T1, T5, T6, T7, T10, T11, T12; FR-4 T10; FR-5 T11; FR-6 T3, T4, T14; FR-7 T5, T7; FR-8 T9, T14; FR-9 T8; FR-10 T8, T14; FR-11 T9; FR-12 T9; FR-13 T1, T7, T12, T14, T17; FR-14 T5; FR-15 T16; FR-16 T16; FR-17 T2, T12, T17; FR-18 T13; FR-19 T1, T13, T15; FR-20 T4, T14. EC-1 T9; EC-2 T9; EC-3 T9; EC-4 T9, T10; EC-5 T8; EC-6 T6, T7, T12, T17; EC-7 T5; EC-8 T5, T6, T7; EC-9 T3, T4; EC-10 T13; EC-11 T13; EC-12 T16; EC-13 T5; EC-14 T8. Unmapped FR/EC: none.

REMEDIATION FREEZE (decision RO-4): T21 is the FINAL remediation round for step 6. After T21 is approved no further code or documentation remediation happens in step 6. Every remaining finding becomes a disclosed Known Limitation in step 7 and step 8. A new issue found while doing T21 is not fixed: it is recorded as a new CR- id with a severity and flows into Known Limitations. Only a High severity security or correctness defect may reopen the freeze, and only after the human is asked explicitly.

T20 note (step 6 follow-up): the original T20 task text named `src/docsync/sanitizer.py` and `tests/test_sanitizer.py`; this was corrected by the human to `src/docsync/redact.py` and `tests/test_redact.py` (decision RO-2 in Section 9), because the codebase and docs/02-architecture.md are authoritative and a second redaction module would duplicate the single redaction function.

Size deviation note (step 5): T13 delivered about 45 lines of production code against the plan's "~40"; accepted at the T13 gate because the parts are tightly coupled.

## 3. Dependency Graph

```mermaid
flowchart LR
    T1 --> T3
    T3 --> T4
    T1 --> T5
    T5 --> T6
    T6 --> T7
    T1 --> T8
    T8 --> T9
    T9 --> T10
    T1 --> T11
    T11 --> T12
    T1 --> T13
    T4 --> T13
    T4 --> T14
    T7 --> T14
    T10 --> T14
    T12 --> T14
    T13 --> T14
    T13 --> T13b
    T13b --> T15
    T14 --> T15
    T15 --> T16
    T16 --> T17
    T16 --> T18
    T2 --> T19
    T17 --> T19
    T18 --> T19
    T4 --> T20
    T19 --> T20
    T20 --> T21
```

The graph is acyclic: every edge goes from a lower-numbered task to a higher-numbered one (the perf fixture decision RO-1 is recorded in Section 9 and is no longer a node).

## 4. Blocked Tasks

| Task | Blocked by | What unblocks it |
|---|---|---|
| T3 | T1 | T1 merged and approved (`errors.py`, `conftest.py` exist) |
| T4 | T3 | T3 approved (redact core and its tests pass) |
| T5 | T1 | T1 approved (`NOT_FOUND`, `ProjectFacts`) |
| T6 | T5 | T5 approved (`collect.py` exists) |
| T7 | T6 | T6 approved (module scan exists) |
| T8 | T1 | T1 approved |
| T9 | T8 | T8 approved (`fetch` decision logic, `FakeSession`) |
| T10 | T9 | T9 approved (HTTP path and failure handling) |
| T11 | T1 | T1 approved (model and sentinel) |
| T12 | T11 | T11 approved (normaliser, sections 1 to 3, 7) |
| T13 | T1, T4 | T1 and T4 approved (errors, full redaction set) |
| T13b | T13 | T13 approved (`parse_args` and `CliArgs` exist) |
| T14 | T4, T7, T10, T12, T13 | All five approved: redactor, collector, GitHub client, renderer, CLI arg layer all present |
| T15 | T14, T13b | T14 and T13b approved (`generate` works end to end and `--out` is validated) |
| T16 | T15 | T15 approved (`generate` works and exit-code handler is in place; `check` only after `generate`) |
| T17 | T16 | T16 approved (both subcommands exist) |
| T18 | T16 | T16 approved (the fixture size was supplied as RO-1) |
| T19 | T2, T17, T18 | `.gitattributes` in place, integration tests pass, perf test exists |
| T20 | T4, T19 | T4 approved (`redact` exists) and T19 approved (step 5 baseline and the step 6 review that raised CR-1 to CR-3) |
| T21 | T20 | T20 approved and the step 6 re-review approved with the freeze decision RO-4 |

T1 and T2 have no blockers and can start immediately.

## 5. Critical Path

Durations are the Est. column. Path: T1 (25) -> T5 (35) -> T6 (30) -> T7 (35) -> T14 (40) -> T15 (30) -> T16 (30) -> T17 (35) -> T19 (20) = 280 minutes.

Comparison of the parallel branches reaching T14: collector branch 125 min (T1, T5, T6, T7), GitHub branch 115 min (T1, T8, T9, T10), redact+CLI-args branch 115 min (T1, T3, T4, T13), render branch 95 min (T1, T11, T12). The collector branch is longest, so it sets the path. T18 (20 min, after T16) runs in parallel with T17 but must also finish before T19; it is off the critical path. Under CLAUDE.md rule 7 the work is serialised one task at a time anyway, so the real elapsed total is the 580-minute sum plus gates.

## 6. Test Plan Mapping

| Test file | Covers task IDs | Covers EC IDs |
|---|---|---|
| `tests/conftest.py` (autouse no-network fixture, shared helpers) | T1 | none (supports NFR-7 for every EC test) |
| `tests/test_model.py` | T1 | EC-6 (defaults exist) |
| `tests/test_redact.py` (each prefix, header, Bearer, URL userinfo, key=value keys, empty and whitespace token, idempotency; T20: bounded quantifiers, every pattern class, ReDoS regression, false positives; T21: more key shapes, structured-text survival) | T3, T4, T20, T21 | EC-9 |
| `tests/test_collect.py` | T5, T6, T7 | EC-6, EC-7, EC-8, EC-13 |
| `tests/test_github.py` (FakeSession; RequestException subclasses; partial payloads) | T8, T9, T10 | EC-1, EC-2, EC-3, EC-4, EC-5, EC-14 |
| `tests/test_render.py` | T11, T12 | EC-6 |
| `tests/test_cli.py` (flags, validation, generate, redaction on file and console, verbose, KeyboardInterrupt/BrokenPipeError exit 2, check exit codes, check read-error exit 2, no-write) | T13, T13b, T14, T15, T16 | EC-10, EC-11, EC-12, EC-9 (console), EC-5, EC-14 (end to end offline) |
| `tests/test_integration.py` | T17, T20 (end-to-end choke-point test) | EC-6, EC-9, EC-12 |
| `tests/test_perf.py` | T18 | none (NFR-1; fixture per RO-1) |
| Command checks (no test file): `ruff check .`, coverage gate, EC naming grep, `git check-attr` | T2, T19 | none |

Binding condition 3 checklist: each redaction pattern (T4, T3), empty token (T3, T8), RequestException subclasses (T9), partial JSON payloads (T10), `check` read-error exit 2 (T16), KeyboardInterrupt/BrokenPipeError exit 2 (T15).

## 7. Risks and Rollback

| Risk | Affected tasks | Response if a task fails |
|---|---|---|
| A task's tests cannot go green | Any | Revert that task's changes only (`git restore` of its files; one commit per task keeps this atomic), do not start the next task, report to the human |
| A task exceeds ~40 lines of production code | Any | Stop and split it into a new numbered sub-task, update this plan, get approval; never batch |
| Redaction over- or under-matches and breaks determinism | T4, T14 | Roll back T4 patterns to T3 core, add the failing sample as a test, fix the pattern; accept false positives over leaks (design review residual risk) |
| `requests` behaviour differs from the fake session | T9 | Keep the fake aligned with `requests.Response` attributes actually used (`status_code`, `json()`); no real network calls to compare (NFR-7) |
| Per-phase timeout can exceed 5 s wall clock (DR-5) | T9, T19 | Not fixed by design (FR-12 mandates the value); report measured online timing in step 7 |
| False drift from CRLF on Windows | T2, T16, T17 | If T2 does not give `eol: lf`, stop and report; do not weaken the byte-compare |
| Wall-clock perf test is flaky on a loaded machine | T18 | The hard threshold is 2.0 s (twice the 1.0 s target) on the best of 3 runs after a warm-up. If it still fails, investigate; do not raise the threshold without human approval. A miss of the 1.0 s target alone is reported, not failed |
| Existing `collectors/` stub conflicts with `collect.py` | T5 | If import ambiguity appears, stop and ask the human (PA-2); do not delete files unprompted |
| Coverage below 85% at T19 | T19 | Add tests in the owning task's test file for the uncovered lines; no coverage-ignore pragmas without approval |
| Rollback of T14 or later after dependents exist | T14 to T17 | Revert in reverse order (latest first) |
| With `--repo` as the root for the `--out` check (T13b), the default `docs/PROJECT_DOCS.md` (resolved against the cwd, ADD-9) was rejected when the cwd was not inside `--repo` | T13b, T14, T17 | **Superseded by the CR-4 decision (step 6, 2026-10-08):** the default is now resolved against the `--repo` root and never depends on the cwd; an explicit relative `--out` still resolves against the cwd and is validated. Code: `cli.py` `parse_args`; docs/01 FR-1 and FR-18, docs/02 section 9 and the README Usage section were updated |

## 8. Out of Plan

| Excluded item | Reason |
|---|---|
| Choosing or changing the NFR-1 fixture size or thresholds without a human decision | Fixed by the human as RO-1 (Section 9); any change needs a new human decision |
| Removing the `src/docsync/collectors/` stub | Not authorised by any requirement; needs human decision (PA-2) |
| Diff output on drift | Rejected in DR-10 (ADD-10) |
| Inferring `--github-repo` from git remotes, any `.git` access | Rejected in DR-11 (ADD-10) |
| Hard wall-clock deadline for HTTP | Not required; FR-12 fixes `timeout=5`; documented residual risk (DR-5) |
| Retry logic, caching, pagination, volatile GitHub fields (stars, forks, issues, push time) | Out of scope per FR-4, FR-12, FR-5 and requirements Section 1 |
| Non-Python projects, non-GitHub platforms, multi-repo runs, publishing docs, editing hand-written prose | Out of scope per requirements Section 1 |
| Running tests of the target repo, `pytest --collect-only` | Rejected in architecture Section 5 (speed, determinism, safety) |
| Writing `docs/PROJECT_DOCS.md`, `CHANGELOG.md`, code review, verification report, PR | Belong to steps 6 to 8 |
| Reading or writing `.env`, keys, credentials | Forbidden by CLAUDE.md rule 6; `.env.example` is not touched by this plan |
| Test-only dependencies (`responses`, `requests-mock`) | Would need approval (architecture Section 5); a hand-written fake is used |

## 9. Resolved Open Items

| ID | Open item | Decision (given by the human at the step 5 T17 gate) | Applied in |
|---|---|---|---|
| RO-1 | NFR-1 performance fixture size and measurement method (A-3, DR-12, OQ-5, PA-4) | Fixture, built in `tmp_path`, offline only, no network, no subprocess: 50 Python modules (5 packages x 10 modules, about 10 lines each); 20 test files with 2 test functions each; `pyproject.toml` declaring 30 runtime dependencies and 5 optional dependencies; a README.md and a LICENSE file. Method: call the generate path in-process (no subprocess, to exclude interpreter startup); one discarded warm-up call; then 3 measured calls with `time.perf_counter`, best (minimum) duration counts; offline forced explicitly (token unset via `monkeypatch.delenv` and `--offline`). Budget: target best run < 1.0 s; test assertion (hard fail) best run < 2.0 s; the test prints the measured best duration so step 7 can quote it. The test carries `@pytest.mark.perf`, registered in `pyproject.toml` because pytest runs with `--strict-markers`; the marker is for selection only and the test stays in the default run | T18; docs/01-requirements.md NFR-1 and Q16 |
| RO-2 | T20 scope after the step 6 review (CR-1, CR-2, CR-3, CR-5): file names, redaction choke point, base64 blob rule, key=value false positives, placeholder | Decided by the human on 2026-10-08. (1) Harden `src/docsync/redact.py` and `tests/test_redact.py` in place; do not create `sanitizer.py` (the original T20 text named the wrong files). (2) `cli.py` remains the single redaction choke point and `render.py` must not call the redactor; an end-to-end test must prove it by asserting on the written file and on captured output; the secret-safety skill was corrected to say so. (3) A bounded base64 blob is redacted only if it contains at least one uppercase letter, one lowercase letter and one digit, a heuristic chosen because the committed document makes a missed secret permanent while a false positive is cosmetic and reversible; tests: a 64-character SHA-256 hex string and a lowercase-only long string are NOT redacted, a mixed-case blob IS. (4) CR-3 is in scope because it shares the key=value regex that must be rewritten for CR-1: `keygen = 1`, `keyring=abc`, `API key: rotate it` and `key = value` are NOT redacted; `api_key=ghp_<token>` and a token-shaped assignment of 20+ characters ARE. (5) CR-5 is resolved by aligning the secret-safety skill to the implemented and architecturally documented placeholder `[REDACTED]`; no code or test is changed for it | T20; `.claude/skills/secret-safety/SKILL.md` (commit `2cfa41a`) |
| RO-3 | CR-4: the default `--out` depended on the current working directory | Decided by the human on 2026-10-08: change the behaviour, not the documentation. Without `--out` the default is `<repo>/docs/PROJECT_DOCS.md`, independent of the cwd; an explicit `--out` resolves against the cwd and keeps the `.md` and inside-`--repo` validation | `src/docsync/cli.py` and `tests/test_cli.py` (commit `546f4b1`); docs/01 FR-1 and FR-18, docs/02 section 9, README Usage (commit `675750f`) |
| RO-4 | Step 6 closure after the re-review (CR-17 to CR-27): which findings are fixed, which are deferred, and the remediation freeze | Decided by the human at the step 6 gate: option 2, a final remediation round T21 and a freeze (see the freeze statement under the task table). **Fixed in T21:** CR-17, CR-19, CR-22 (code), CR-23, CR-24, CR-25 (documents that contradict the code) and the date method (CR-28, below). **Deferred, to be disclosed as Known Limitations:** CR-7 to CR-16, CR-18, CR-20 and CR-21 by the human's decision, and CR-26 and CR-27 by the freeze rule; each is recorded in docs/05-code-review.md section 7.7 with its severity and a one-line justification, and must reappear verbatim in the Known Limitations sections of docs/06-verification.md and docs/07-pr-description.md. **pip-audit note for step 7:** `pip-audit` skipping the local project because it is not published on PyPI is expected behaviour, not a defect; step 7 states which dependencies WERE audited (runtime and dev) and that the local editable package is out of scope for a vulnerability database lookup | T21; docs/05-code-review.md section 7.7; steps 7 and 8 |

## 10. Environment Limitations

Known limitations of the environment the tests were run in. Steps 7 and 8 must carry each entry into the verification report and the PR description as a Known Limitation, not as an unexplained gap. Step 7 must reproduce EL-1 to EL-3 in the Known Limitations section of docs/06-verification.md, together with the deferred findings listed in docs/05-code-review.md section 7.7 (decision RO-4), verbatim.

| ID | Limitation | Affected test | Impact | How it is handled |
|---|---|---|---|---|
| EL-1 | Directory symlinks cannot be created on the development machine (Windows without elevated privileges or Developer Mode) | `tests/test_collect.py::test_scan_modules_symlinked_directory_is_not_followed` (T6; ADD-8, DR-9 "symlinked directories are not followed") | The test is skipped here, so "symlinked directories are not followed" is implemented (`os.walk(followlinks=False)` plus an explicit `is_symlink()` prune) but not exercised by a passing test on this machine | The skip is declared with `skipif` and an explicit reason (EL-1); it runs wherever symlinks can be created (for example Linux CI). Step 7 must record the skip in the verification report; whether it is covered by a manual or CI run is `Not Found` until step 7 produces that evidence |
| EL-2 | The directory-creation-order determinism test cannot fail on NTFS, because NTFS enumerates directory entries in sorted order | `tests/test_integration.py::test_document_does_not_depend_on_file_creation_order` (T17; NFR-8, ADD-3) | On this machine the test cannot detect an ordering defect. It would only catch a real defect on a filesystem that returns unsorted entries (typical on Linux and CI) | Ordering is covered directly in T6 (`test_scan_modules_output_sorted_by_code_point`, `Z` before `a`). Step 7 should run the suite on a Linux/CI filesystem if one is available; otherwise record the gap as a Known Limitation |
| EL-3 | No test exercises the live GitHub API, by design (NFR-7: no real network calls in tests) | `tests/test_github.py`, `tests/test_cli.py` (T9, T10, T14) | Real-network behaviour (TLS, redirects, actual response shape and rate limits) is not verified by the automated suite | Online behaviour is covered with fake sessions in T9, T10 and T14, and the autouse fixture makes any real call fail the test. Whether a manual online run is done is `Not Found` until step 7 produces that evidence |

Recorded at T17: the full test suite runs in approximately 4.7 s on the development machine, dominated by 5 subprocess tests (`python -m docsync` runs). This is a measured observation, not a requirement.

---
**Gate:** Approve step 4 and continue? (yes / changes needed)
