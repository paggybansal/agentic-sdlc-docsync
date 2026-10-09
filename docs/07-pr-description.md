# Pull Request Description — DS-1 Automated Documentation Sync

| Field | Value |
|---|---|
| Artifact | docs/07-pr-description.md |
| SDLC Step | 8 — Pull Request |
| Source documents | docs/01-requirements.md to docs/06-verification.md, CHANGELOG.md, `git log`, `git diff main...HEAD --stat` |
| Author | pr-author (main thread) |
| Date | 2026-10-09 (`git log -1 --format=%cs e6aa7be`) |
| Status | Draft |

Branch `feature/DS-1-docsync` into `main`.

## Summary

This PR delivers work item DS-1 in two layers: an eight-step Agentic SDLC pipeline built with Claude Code (eight subagents, three skills, three slash commands, two enforcement hooks, `CLAUDE.md`), and the feature that pipeline produced, `docsync`, a Python CLI whose `generate` and `check` commands keep `docs/PROJECT_DOCS.md` in sync with the repository and, optionally, its GitHub metadata. The tool is offline-first, redacts secrets before anything is written or printed, and is checked by its own CI gate against the committed document.

## Changes Made

Derived from `git diff main...HEAD --name-status` (51 files at `e6aa7be`) plus the files added or modified by this step. `evidence/` is not part of the PR: it is listed in `.gitignore` (commit `e6aa7be`) and is untracked.

### Pipeline (`.claude/`, `CLAUDE.md`)

- `CLAUDE.md` (added): always-on rules: gates, traceability, secrets policy, commit format, git-derived dates.
- `.claude/AGENTIC_SDLC_PROCESS.md` (added): authoritative process definition.
- `.claude/agents/1-requirements-analyst.md` to `.claude/agents/8-pr-author.md` (8 files added): one role contract per SDLC step.
- `.claude/commands/sdlc-run.md`, `sdlc-status.md`, `sdlc-step.md` (3 files added): orchestrate, report status, run one step.
- `.claude/hooks/block_secrets.py` (added): PreToolUse hook that denies writes to secret files.
- `.claude/hooks/run_tests.py` (added): PostToolUse hook that runs pytest after `src/` or `tests/` edits.
- `.claude/settings.json` (added): hook registration and permissions.
- `.claude/skills/python-test-standards/SKILL.md`, `.claude/skills/sdlc-doc-templates/SKILL.md`, `.claude/skills/secret-safety/SKILL.md` (3 files added): reusable know-how.
- `.gitattributes` (added): pins `docs/PROJECT_DOCS.md` to LF (FR-17).
- `.gitignore` (modified): adds `evidence/` and rewrites the `.claude/backups/` line ending.
- `.env.example` (modified): a comment line added and the `DOCSYNC_HTTP_TIMEOUT` line rewritten (placeholders only, no values).

### Product (`src/`, `tests/`, `pyproject.toml`, `.github/`)

- `src/docsync/__main__.py` (added): `python -m docsync` entry point (T15).
- `src/docsync/cli.py` (added): argument parsing, `--out` validation, `generate` and `check`, top-level error handler, redaction choke point (T13, T13b, T14, T15, T16).
- `src/docsync/collect.py` (added): `pyproject.toml` facts, static module and test scan (T5 to T7).
- `src/docsync/errors.py` (added): domain errors (T1).
- `src/docsync/github.py` (added): token-gated hosted-metadata fetch with degraded failure handling (T8 to T10).
- `src/docsync/model.py` (added): `ProjectFacts` and the `Not Found` sentinel (T1).
- `src/docsync/redact.py` (added): secret redaction (T3, T4, T20, T21a, T22).
- `src/docsync/render.py` (added): deterministic seven-section renderer (T11, T12).
- `src/docsync/collectors/__init__.py` (deleted): dead step-0 stub, removed per RO-2.
- `tests/conftest.py` (added): autouse fixture that blocks real network calls (NFR-7).
- `tests/test_cli.py`, `tests/test_collect.py`, `tests/test_github.py`, `tests/test_integration.py`, `tests/test_model.py`, `tests/test_perf.py`, `tests/test_redact.py`, `tests/test_render.py` (8 files added): the pytest suite, with EC ids in test names (NFR-4).
- `pyproject.toml` (modified): registers the `perf` pytest marker.
- `.github/workflows/ci.yml` (added): CI matrix, advisory `pip-audit`, documentation sync gate.

### Documentation (`docs/`, `CHANGELOG.md`, `README.md`, `LICENSE`, `evidence/`)

- `docs/01-requirements.md`, `docs/02-architecture.md`, `docs/03-design-review.md`, `docs/04-impl-plan.md`, `docs/05-code-review.md`, `docs/06-verification.md` (6 files added): SDLC artifacts for steps 1 to 7.
- `docs/PROJECT_DOCS.md` (added): the committed offline rendering produced by `docsync generate`; the CI gate checks it.
- `docs/07-pr-description.md` (added, this step): this document.
- `CHANGELOG.md` (modified, this step): `[Unreleased]` entries for DS-1.
- `README.md` (modified): documents the two layers, artifacts, usage and the `--out` default.
- `LICENSE` (added): MIT, copyright 2026 Parag Bansal.
- `evidence/` (not in the PR): six local transcripts, ignored by `.gitignore`.

## Test Evidence

All figures below appear in `docs/06-verification.md`; local commands were re-run at `e6aa7be` (Windows 11, Python 3.14.2). Items marked human-supplied were read by the human from the CI job log.

### CI (GitHub Actions)

- Run: https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702, event `push` on commit `c8489911bfd284d8b5b13f67433c442e87d89602`, conclusion `success`.
- All five jobs `success`: test (ubuntu-latest / py3.11), test (ubuntu-latest / py3.12), test (windows-latest / py3.11), test (windows-latest / py3.12), dependency audit (advisory).
- This run predates the step 7 and step 8 commits. A CI run on the final PR head: `Not Found` (it runs when the branch is pushed).
- ubuntu-latest / py3.12 (human-supplied; the verifier could not read the logs, HTTP 403): `456 passed`, 0 skipped. Coverage TOTAL 339 statements, 6 missed, 98%; uncovered: `__main__.py` 3-8 and `collect.py` 111->108, 131-132. The full per-file Linux coverage table and the exact summary line with timing: `Not Found` (not available to the verifier).

### Local pytest and coverage (verbatim, after the RO-2 deletion)

```text
$ python -m pytest -q --cov=src/docsync --cov-report=term-missing
_______________ coverage: platform win32, python 3.14.2-final-0 _______________

Name                      Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------
src\docsync\__init__.py       1      0      0      0   100%
src\docsync\__main__.py       4      4      2      0     0%   3-8
src\docsync\cli.py          102      0     16      0   100%
src\docsync\collect.py       79      2     14      1    97%   111->108, 131-132
src\docsync\errors.py         4      0      0      0   100%
src\docsync\github.py        47      0      8      0   100%
src\docsync\model.py          6      0      0      0   100%
src\docsync\redact.py        33      0      6      0   100%
src\docsync\render.py        42      0      4      0   100%
---------------------------------------------------------------------
TOTAL                       318      6     50      1    98%
======================= 455 passed, 1 skipped in 5.90s ========================
```

NFR-3 target is 85%; measured 98% locally and 98% on Linux CI. NFR-1: the perf test printed `[perf] offline generate best of 3: 0.0140 s (all: 0.0143, 0.0140, 0.0166); target < 1.0 s: target met; hard limit < 2.0 s`.

### Static analysis

- `ruff check .`: `All checks passed!` (exit 0).
- `pip-audit`: `No known vulnerabilities found` (exit 0). Audited the installed versions: requests 2.34.2, urllib3 2.8.0, certifi 2026.7.22, idna 3.20, charset-normalizer 3.5.2 (plus pytest 9.1.1, pytest-cov 7.1.0, ruff 0.16.10 and their dependencies). The local editable package `docsync (0.1.0)` was skipped as expected (not on PyPI). The declared floor `requests>=2.32.0` was not audited (RO-10).
- `docsync check --repo . --out docs/PROJECT_DOCS.md`: `in sync`, exit 0 (re-run in this step).

### Functional verification (docs/06-verification.md section 4)

| V-ID | Outcome | Exit code |
|---|---|---|
| V-1 | Pass: happy path, offline | 0 |
| V-2 | Pass: idempotency; `git diff --stat -- docs/PROJECT_DOCS.md` empty with the file tracked, `cmp` byte-identical | 0 |
| V-3 | Pass: `check` printed `in sync` | 0 |
| V-4 | Pass: drift gave exit 1; file restored; `in sync` afterwards | 1 (drift), 0 (restored) |
| V-5 | Pass: empty repository, 7 sections, every field `Not Found` except the two Generation Info versions | 0 |
| V-6 | Pass: invalid input, one-line message, no traceback | 2, 2, 2 |
| V-7a, V-7b | Pass: invalid token (HTTP 401) and unreachable host each gave one warning and `Not Found` | 0, 0 |
| V-8 | Pass: fake token-shaped values redacted in the file, stdout and stderr | 0 |
| V-9 | Pass: `grep -c REDACTED docs/PROJECT_DOCS.md` printed `0` | 0 |
| V-10 | NFR-2 online figure `Not Found`: with the token unset the tool makes no request (FR-9, EC-5); wall time 0.834 s, all six hosted fields `Not Found`; EC-5 demonstrated | 0 |
| V-11 | Not run: the manual authenticated live run is pending the human (docs/06-verification.md section 4.1); result `Pending - human to run` | Not Found |

### EL-1 and EL-2 closure (human-supplied CI evidence)

ubuntu-latest / py3.12 reported 456 passed and 0 skipped against 455 passed and 1 skipped on Windows, so the symlink test that skips on Windows ran and passed on Linux (EL-1), and the full suite, including the directory-creation-order test, passed on ext4 rather than NTFS (EL-2); the Windows skip is environmental (`OSError [WinError 1314] A required privilege is not held by the client`).

### NFR-2

Offline figure: 0.0140 s best of 3 against the 1.0 s target (`tests/test_perf.py`). Online figure: `Not Found` (V-11 pending; the curl HTTP 200 in 0.437647 s is corroborating side evidence only and does not time `docsync`).

## Known Limitations

Verification verdict: `Pass with limitations` (docs/06-verification.md section 9), conditional only on V-11 being run and recorded by the human.

### Offline-rendering invariant

The committed docs/PROJECT_DOCS.md is the offline rendering. An authenticated run resolves the six hosted fields and therefore reports drift against the committed offline artifact. Both CI and the committed artifact use offline mode; mixing modes between generate and check is a configuration error, not a tool defect.

### Fields that legitimately render `Not Found` (docs/06-verification.md section 8.1, verbatim)

| Where | Field | Why |
|---|---|---|
| docs/PROJECT_DOCS.md, Identity & Metadata | License | This repository's `pyproject.toml` declares no license. Adding a `LICENSE` file (commit `91fdad9`) did not change this: the tool reads only `pyproject.toml` (FR-7, `test_collect_pyproject_opens_only_pyproject`), so the field stays `Not Found`; regenerating produced an empty `git diff` |
| docs/PROJECT_DOCS.md, Identity & Metadata | Authors | This repository's `pyproject.toml` declares no authors |
| docs/PROJECT_DOCS.md, Hosted Repository Metadata | Full Name, Description, Default Branch, Visibility, License, Topics | Offline mode: no token and no `--github-repo` supplied, so no request is made (FR-9, EC-5, EC-14) |
| NFR-2 | Online wall-clock time of a successful lookup | `Pending V-11`: not observable without a token (FR-9, EC-5; V-10 showed this); the human's manual authenticated run V-11 will supply the figure. Until then it is `Not Found` |
| docs/04-impl-plan.md | Estimates of T20, T21, T22 | `Not Found` permanently by human decision (RO-7); step 8 discloses it as a process limitation |
| EL-1, EL-2 | Per-test result of the symlink test and the directory-order test on Linux CI | Closed by human-supplied CI evidence (section 3.2); no longer `Not Found` |

Also `Not Found` or out of scope: line-ending normalisation (EL-4, docs/06-verification.md section 1): git stores LF for every tracked text file, 31 tracked files are CRLF in the author's working copy (`core.autocrlf=true`), and only `docs/PROJECT_DOCS.md` is pinned to LF by `.gitattributes`; no repo-wide normalisation is done. The NFR-2 online figure and the V-11 results are `Pending - human to run`. The Linux per-file coverage table and exact summary line are `Not Found`.

### Environment limitations and dependency floor (docs/06-verification.md section 8.2, verbatim)

| ID | Limitation | Evidence from this step |
|---|---|---|
| EL-1 | CLOSED (human-supplied CI evidence). Directory symlinks cannot be created on the Windows development machine, so `test_scan_modules_symlinked_directory_is_not_followed` is skipped there | Windows manual attempt: `OSError [WinError 1314] A required privilege is not held by the client` (paths omitted); environmental. Linux: ubuntu-latest / py3.12 reported 456 passed, 0 skipped against 455 passed, 1 skipped locally, so the test executed and passed on Linux (section 3.2) |
| EL-2 | CLOSED (human-supplied CI evidence). The directory-creation-order determinism test cannot fail on NTFS | The full suite ran on ubuntu-latest (ext4) with zero failures, so `test_document_does_not_depend_on_file_creation_order` ran and passed there (section 3.2). Ordering is also covered directly by `test_scan_modules_output_sorted_by_code_point` |
| EL-3 | No automated test exercises the live GitHub API, by design (NFR-7) | V-7a and V-7b exercised failure paths manually; V-10 showed an unauthenticated online lookup is impossible (FR-9, EC-5); a successful online lookup was not observed; V-11 is the planned manual closure (section 4.1) |
| RO-10 | Dependency floor | Only the installed dependency versions were audited: requests 2.34.2, urllib3 2.8.0, certifi 2026.7.22, idna 3.20, charset-normalizer 3.5.2 (plus pytest 9.1.1, pytest-cov 7.1.0, ruff 0.16.10 and their dependencies). The declared lower bound requests>=2.32.0 was not independently audited; a consumer resolving to the floor version is outside the verified configuration. The local editable package `docsync (0.1.0)` is out of scope for a vulnerability database lookup |

### Deferred findings (verbatim from docs/06-verification.md section 8.3; CR-33 excluded, it was resolved in T22)

Status for every row: Deferred, disclosed as Known Limitation.

| CR id | Severity | Finding (short) | Justification for deferral |
|---|---|---|---|
| CR-7 | Minor | Duplicated helpers (`_text`, `_license`, string-list helpers, the token and env expressions in `cli.py`) | Behaviour is correct and tested; consolidating touches three modules after the freeze |
| CR-8 | Minor | An undecodable test file is reported as a "syntax error" | The count and exit code are right; only the warning wording is imprecise |
| CR-9 | Info | Empty `collectors/` stub; `CollectError` and `GitHubError` are never raised | PA-2 awaits a human decision; no behaviour impact |
| CR-10 | Minor | Weak tests (test doubles, source-grep tests, one multi-assert test, `__main__.py` at 0% line coverage) | Behaviour is guarded by other tests; strengthening is quality work, not a defect fix |
| CR-11 | Info | EL-1 (symlink test skipped), EL-2 (NTFS ordering) and EL-3 (no live API test) | Environment limits, disclosed by design in docs/04 section 10 |
| CR-12 | Minor | `--out` residuals: `CON.md`, `.git/x.md` and overwriting an existing in-repo `.md` such as `README.md` are accepted | Inside `--repo` and `.md` only, so not a traversal; a stricter rule needs a policy decision |
| CR-13 | Info | The final `except Exception` carries `# noqa: BLE001` (already Accepted in section 3) | Mandated by FR-19 |
| CR-14 | Info | Some planned test names in docs/01 differ from the implemented names | Traceability by requirement id is intact |
| CR-15 | Info | `tests/test_cli.py` is very large and repeats a fake-token literal | Split when next touched |
| CR-16 | Info | Secret-scan matches are deliberate fake fixtures and the detection regex (already Accepted) | No real credential exists in the repository |
| CR-18 | Minor | The strong-key rule redacts ordinary prose such as `the password: required` | Accepted trade-off: a missed secret in a committed document is permanent, a false positive is cosmetic (RO-2) |
| CR-20 | Minor | Base64 runs over 4,096 characters leave a final fragment under 40 characters; base64url is not covered; long PEM bodies leave a tail | Far beyond the sizes of generated metadata; the bounds are what keep the work linear |
| CR-21 | Minor | URL userinfo residuals (`p@ss`, a `/` inside a password) | Rare in committed metadata; widening the rule risks the bounded-time guarantee |
| CR-26 | Info | A very short literal secret corrupts other text | Needs a one-character token; unrealistic (freeze rule) |
| CR-27 | Info | The 13 rules in `_RULES` are unnamed (correction recorded in 7.7.3: the real count is 14, 13 explicit plus 1 heuristic; the finding itself is unchanged) | Readability only (freeze rule) |
| CR-29 | Info | New: a long camel-case identifier of 40 or more characters containing a digit is redacted by the blob heuristic | Cannot be separated from random base64 by entropy (measured: identifiers 4.2 to 4.4 bits, random base64 4.3 and above); excluding it would miss real secrets |
| CR-30 | Minor | New: the widened key rules redact configuration names and table headers: `max_tokens = 4096` becomes `max_tokens = [REDACTED]`, and a header cell pair `\| Secret \| Description \|` becomes `\| Secret \| [REDACTED] \|` | Cosmetic and reversible; plural and suffixed key names are exactly what CR-17 asked to catch. V-9 passed on this repository's real document (0 occurrences of `[REDACTED]`), so CR-30 is not escalated |
| CR-31 | Info | New: secrets pasted together with no delimiter are not idempotent (`AKIA...EXAMPLEsk-ant-...`), because replacing the first changes the character the second one is anchored to | Measured at 0.11% to 0.14% of structured fuzz strings and 0 of 150,000 when delimited; the first pass already hides both. RO-6 reasoning, verbatim: "Redaction is applied to the same raw source input on every run and is never re-applied to already-redacted text. Document idempotency (AC7) is therefore unaffected; the non-idempotency is confined to repeated redaction of a single string in memory." |
| CR-32 | Info | New: the path-like heuristic can skip a random base64 secret that has several long mostly lower-case segments | Measured: 3 of 159,922 random mixed-case base64 secrets (0.002%) were skipped |
| CR-34 | Info | New: an unquoted secret value that contains `}` is redacted only up to the brace | The brace stop keeps JSON structure intact and the output idempotent |
| CR-35 | Minor | `sk-` package names such as `sk-learn-extension-package-name` are redacted (a consequence of the human's ruling that a prefix match is sufficient for explicit patterns) | A false positive on non-secret text; cosmetic and reversible, and the ruling prefers it to a missed credential |
| CR-38 | Info | Anchor, case and length residuals for prefixed tokens: `sk-` directly after a letter or digit, upper-case `SK-`, `GHP_` and `XOXB-`, a 15-character `sk-` body, `xoxe-` tokens, an `AKIA` token with extra characters, a token split by a newline. Under the human's later standing triage rule some of these count as security false negatives; the human was told so and chose to defer | Deferred by the human's explicit decision. The residuals come from anchoring and length bounds, are very rare in repository metadata, and a fix would reopen the redactor under the remediation freeze |
| CR-39 | Info | docs/04-impl-plan.md, T21 row: the goal text of T21a lists "long camel-case identifiers" and "`sk-` package names" among the structured text it would stop mangling; the shipped redactor does neither (CR-29, CR-35) | Auto-deferred: Info, a statement of task intent in a historical record, no code or generated-document effect. The authoritative status of both items is recorded in 7.7.2 (CR-29) and 7.8.6 (CR-35) |
| CR-40 | Info | docs/04-impl-plan.md, T4 row: the T4 task description says the `key=value` rule applies to `key` among the strong words; the shipped bare-`key` rule needs a token-shaped value of 20 or more characters | Auto-deferred: Info, a historical task description superseded by T20 and T21a. docs/02-architecture.md section 7 (revision 1.4) states the current rules |
| CR-41 | Info | docs/03-design-review.md, risk register: the risk example that `key=value` redaction "may over-redact benign text (for example `monkey=...`)" no longer happens: a bare `key` now needs a 20 or more character value | Auto-deferred: Info, a review-time risk example in a historical record; the document is not modified after step 3. The risk was accepted at step 3 and has since been reduced |
| CR-42 | Minor | New, raised in step 7 (V-10): the CLI has no unauthenticated-online mode, so public repositories cannot be read without a token (FR-9 / EC-5 behaviour is token-gated). Disclosed as a future enhancement | Deferred under the remediation freeze and RO-11 (Minor, no accepted AC broken, no security effect); FR-9 and EC-5 require this behaviour, so it is a requirement trade-off and not a defect |
| CR-43 | Minor | New, raised in step 7 (coverage review): `src/docsync/collect.py` branch `111->108`, the case in `_count_tests` where a top-level statement in a test file is neither a test function nor a class, is never executed by any test. No existing CR id names it: CR-8 and CR-10 name only lines 131-132 (the `OSError` branch when reading a test file), and those lines are already covered by those two ids, so they need no new id. Disclosed; step 8 PR must carry it | Deferred under the remediation freeze and RO-11 (Minor, no accepted AC broken, no security effect); the surrounding counting behaviour is exercised by other tests and an untested loop-continue branch does not change results. Recorded here only, not in docs/05-code-review.md |
| CR-44 | Minor | New, raised in step 8 (pre-flight): the local verification environment runs CPython 3.14.2, which is outside the CI matrix (3.11 and 3.12 on ubuntu-latest and windows-latest). The full suite passes on 3.14.2 locally (455 passed, 1 skipped) but 3.14 is not continuously verified. Extending the CI matrix to 3.13 and 3.14 is a future enhancement | Deferred under the remediation freeze and RO-11 (Minor, no accepted AC broken, no security effect). Recorded in this document only; docs/05-code-review.md and docs/06-verification.md section 8.3 were not edited |

### Other limitations (docs/06-verification.md section 8.4, verbatim)

| Item | Detail |
|---|---|
| Static test counts | The Test Suite Summary counts `test_*` functions statically (262) and does not equal pytest's collected item count (456) |
| `check` for CI | Not run in a CI environment in this session; the CI run in section 3.1 ran `generate` then `check` offline and passed |
| Committed artifact is offline (FIX 1c) | The committed docs/PROJECT_DOCS.md is the offline rendering. An authenticated run resolves the six hosted fields and therefore reports drift against the committed offline artifact. Both CI and the committed artifact use offline mode; mixing modes between generate and check is a configuration error, not a tool defect. |

## Reviewer Checklist

- [ ] Correctness: behaviour matches `docs/01-requirements.md` (FR-1..FR-20, EC-1..EC-14)
- [ ] Security: no secrets in code, logs or generated output; user input validated; deferred redaction residuals reviewed
- [ ] Error Handling: API failures, missing files and an empty repository are handled gracefully (exit codes 0, 1, 2; no tracebacks)
- [ ] Test Coverage: tests cover the happy path and the `Not Found` / missing-field cases; coverage 98% against the 85% target
- [ ] Code Clarity: function names are self-explanatory and logic is readable without comments
- [ ] DRY: no duplicated logic that should be shared (CR-7 deferred)
- [ ] Dependency Safety: no known-vulnerable dependency versions (`pip-audit` clean for the installed versions; floor `requests>=2.32.0` not audited)
- [ ] Artifacts 01 to 07 present and consistent
- [ ] No secrets committed
- [ ] Hooks present and demonstrated (`.claude/hooks/block_secrets.py`, `.claude/hooks/run_tests.py`)
- [ ] `docsync check` exits 0 on the committed artifact
- [ ] CI green on all five jobs (including on the final PR head)
- [ ] Known Limitations reviewed and accepted

## Traceability

| SDLC Step | Agent | Artifact | Commit |
|---|---|---|---|
| 0 | Not Found (human scaffold) | `.claude/`, `CLAUDE.md`, `input/DS-1-user-story.md` | c848991 |
| 1 | requirements-analyst | docs/01-requirements.md | 6d79f71 (later edits f7eff16) |
| 2 | solution-architect | docs/02-architecture.md | 2523db4 (latest edit 535233d) |
| 3 | design-reviewer | docs/03-design-review.md | 3bbd2c0 |
| 4 | impl-planner | docs/04-impl-plan.md | 0940ccc (latest edit 8cc0ff3) |
| 5 | implementer | `src/`, `tests/` | 202bc99 (T1) to 3487008 (T22); bbc142c (RO-2) |
| 6 | code-reviewer | docs/05-code-review.md | 03a965c (initial), d8fb7de (re-review), c416247 (delta re-review), 111861f (closure) |
| 7 | verifier | docs/06-verification.md, docs/PROJECT_DOCS.md | 27b00d1, 0c334f2, e6aa7be (9a84131 by the human) |
| 8 | pr-author | docs/07-pr-description.md, CHANGELOG.md | Not Found (committed after approval) |

## Agentic SDLC Notes

- **Hybrid execution model.** Steps 1, 5 and 8 run in the main thread because subagents cannot pause to ask the human questions; steps 2, 3, 4, 6 and 7 are delegated to subagents. Every step ends at a human gate (`Approve step <N> and continue? (yes / changes needed)`).
- **Hooks.** `block_secrets.py` (PreToolUse on Write/Edit) denies writes to `.env`, `*.pem`, `*.key`, `secrets.*` and `credentials.*`. `run_tests.py` (PostToolUse on Write/Edit) runs `pytest -q` after any `src/` or `tests/` change and feeds failures back to the agent.
- **Remediation freeze (RO-4).** T21 was declared the final remediation round for step 6 so that review could converge: after it, every remaining finding is disclosed as a Known Limitation instead of fixed. Only a High-severity security or correctness defect may reopen it, and only with the human's explicit approval; this is why the deferred register above is long and carried verbatim.
- **Review-fix-re-review loop.** The initial review (03a965c) returned `Changes requested` with CR-1 (ReDoS) and CR-2 (missing secret shapes) blocking. They were fixed together with CR-3 in T20 (9e52a1d); CR-4 by 546f4b1 and 675750f; CR-5 by 2cfa41a; the re-review (d8fb7de) returned `Approved`. CR-33 (High, a security false negative found afterwards) was the single freeze exception: fixed in T22 (3487008) and verified by the delta re-review (c416247), whose closing verdict for step 6 is `Approved`.
