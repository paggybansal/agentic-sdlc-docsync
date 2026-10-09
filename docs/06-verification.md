# Verification Report — DS-1 Automated Documentation Sync

| Field | Value |
|---|---|
| Artifact | docs/06-verification.md |
| SDLC Step | 7 — Verification |
| Source documents | docs/01-requirements.md, docs/04-impl-plan.md (RO-5 to RO-11, EL-1 to EL-4), docs/05-code-review.md (sections 7.7 to 7.11), CLAUDE.md, .claude/agents/7-verifier.md |
| Author | verifier |
| Date | 2026-10-09 (`git log -1 --format=%cs c848991`) |
| Status | Draft |

## 1. Environment

| Item | Value |
|---|---|
| OS | Microsoft Windows 11 Enterprise, `ver`: `Microsoft Windows [Version 10.0.26200.9457]`; commands run in Git Bash (`MINGW64_NT-10.0-26200`) |
| Python | 3.14.2 |
| Commit hash | `c848991` for the first verification run (`git rev-parse --short HEAD`), branch `feature/DS-1-docsync`. Later commits made during step 7 at the human's direction: `27b00d1` (track PROJECT_DOCS.md), `91fdad9` (LICENSE), `9a84131` (human commit "add verification file.", which added an earlier version of this file), `bbc142c` (remove dead collectors package, RO-2), `0c334f2` (regenerate PROJECT_DOCS.md). Post-deletion figures below were measured on `0c334f2` |
| Commit date | 2026-10-09 (`git log -1 --format=%cs HEAD`) |
| Tools | pytest 9.1.1, pytest-cov 7.1.0, ruff 0.16.10 |
| Runtime dependencies as installed | requests 2.34.2, urllib3 2.8.0, certifi 2026.7.22, idna 3.20, charset-normalizer 3.5.2 |
| `DOCSYNC_GITHUB_TOKEN` at start | not set (only set / not set is reported; no value was read) |
| EL-4 (line endings, disclosed here, not a section 8 limitation, as docs/04 section 10 requires) | `git config core.autocrlf` printed `true`. `git ls-files --eol`, counted by index/worktree state: `31 i/lf w/crlf`, `22 i/lf w/lf`, `1 i/none w/none`. So git stores LF for every tracked text file (`i/lf`) while 31 tracked files are CRLF in this working copy (`w/crlf`); the rest, for example `docs/04-impl-plan.md` and `src/docsync/cli.py`, are LF in the working copy. There is deliberately no repo-wide `.gitattributes` normalisation. Only `docs/PROJECT_DOCS.md` is pinned: `git check-attr eol docs/PROJECT_DOCS.md` printed `docs/PROJECT_DOCS.md: eol: lf`; the generated file contains 0 `\r` bytes (section 5) |
| Working tree before the run | Only the six pre-existing untracked files under `evidence/` |

## 2. Static Analysis Results

```text
$ ruff check .
All checks passed!
exit=0
```

```text
$ python -m pip_audit        (the `pip-audit` entry point is installed in .venv; same tool)
No known vulnerabilities found
Name    Skip Reason
------- ----------------------------------------------------------------------
docsync Dependency not found on PyPI and could not be audited: docsync (0.1.0)
exit=0
```

pip-audit scope (RO-4, RO-10). Audited: the installed runtime and dev dependencies of the active environment (requests 2.34.2, urllib3 2.8.0, certifi 2026.7.22, idna 3.20, charset-normalizer 3.5.2, pytest, pytest-cov, ruff and their dependencies). Not audited: the local editable package `docsync (0.1.0)`, which is not on PyPI, so skipping it is expected behaviour and not a defect.

## 3. Test Execution Evidence

Run 1, at `c848991`, BEFORE the RO-2 deletion (superseded for coverage by run 2 below; kept as the original record):

```text
$ python -m pytest -q --cov=src/docsync --cov-report=term-missing
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\parag_bansal\PycharmProjects\GitHub\agentic-sdlc-docsync
configfile: pyproject.toml
testpaths: tests
plugins: platformdirs-4.12.3, cov-7.1.0
collected 456 items

tests\test_cli.py ...................................................... [ 11%]
...............................................                          [ 22%]
tests\test_collect.py .............................s...............      [ 32%]
tests\test_github.py ................................................... [ 43%]
............                                                             [ 45%]
tests\test_integration.py .............                                  [ 48%]
tests\test_model.py ..........                                           [ 50%]
tests\test_perf.py .
[perf] offline generate best of 3: 0.0174 s (all: 0.0185, 0.0174, 0.0174); target < 1.0 s: target met; hard limit < 2.0 s
.                                                    [ 51%]
tests\test_redact.py ................................................... [ 62%]
........................................................................ [ 78%]
..............................................................           [ 91%]
tests\test_render.py .....................................               [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.14.2-final-0 _______________

Name                                 Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------------------------
src\docsync\__init__.py                  1      0      0      0   100%
src\docsync\__main__.py                  4      4      2      0     0%   3-8
src\docsync\cli.py                     102      0     16      0   100%
src\docsync\collect.py                  79      2     14      1    97%   111->108, 131-132
src\docsync\collectors\__init__.py       0      0      0      0   100%
src\docsync\errors.py                    4      0      0      0   100%
src\docsync\github.py                   47      0      8      0   100%
src\docsync\model.py                     6      0      0      0   100%
src\docsync\redact.py                   33      0      6      0   100%
src\docsync\render.py                   42      0      4      0   100%
--------------------------------------------------------------------------------
TOTAL                                  318      6     50      1    98%
======================= 455 passed, 1 skipped in 6.79s ========================
exit=0
```

Run 2, local Windows, AFTER the RO-2 deletion of `src/docsync/collectors/` (commit `bbc142c`; `ruff check .` printed `All checks passed!`, exit 0). Tail of the real output, which replaces the run 1 coverage table:

```text
$ python -m pytest -q --cov=src/docsync --cov-report=term-missing   (tail)
tests\test_redact.py ................................................... [ 62%]
........................................................................ [ 78%]
..............................................................           [ 91%]
tests\test_render.py .....................................               [100%]

=============================== tests coverage ================================
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
TOTAL                      318      6     50      1    98%
======================= 455 passed, 1 skipped in 6.76s ========================
```

New local coverage total: 98% (318 statements, 6 missed); unchanged because the deleted module had 0 statements. The `collectors/__init__.py` row is gone. The later run also printed `collected 456 items` and `[perf] offline generate best of 3: 0.0140 s (all: 0.0175, 0.0140, 0.0786)`, so the current NFR-1 figure is 0.0140 s (earlier 0.0174 s).

RO-2 was found incomplete during verification: `src/docsync/collectors/__init__.py`, an empty stub, was still present (CR-9, PA-2). The human decided to remove it. `git grep -n "collectors" -- src tests docs .github` found no import of the package: the hits were prose in docs/02, docs/04, docs/05, docs/06 and docs/PROJECT_DOCS.md, two path strings used as redaction test fixtures (`tests/test_redact.py:363` and `:753`), and one docstring (`tests/test_render.py:219`). The stub was removed with `git rm -r` (commit `bbc142c`, one file, 0 lines), the module row disappeared from `docs/PROJECT_DOCS.md` (diff: one deleted line `| Module | src/docsync/collectors/__init__.py |`), and `docsync check` returned `in sync`, exit 0, after regeneration (commit `0c334f2`).

Linux CI coverage (human-supplied, read from the `test (ubuntu-latest / py3.12)` job, measured BEFORE the deletion; the verifier did not measure it): TOTAL 339 statements, 6 missed, 98%, which exceeds the NFR-3 target of 85%. Uncovered: `__main__.py` 3-8 (CR-10, deferred) and `collect.py` 111->108 and 131-132 (see CR-8, CR-10 and CR-43 in section 8.3). The Windows and Linux statement totals differ (318 against 339); the reason was not investigated. The Windows figures stay separate from the Linux figure.

Skip reason (`python -m pytest -q -rs`, filtered with `grep -i skip`):

```text
SKIPPED [1] tests\test_collect.py:273: EL-1: directory symlink creation is not permitted in this environment (Windows needs elevated privileges or Developer Mode); see docs/04-impl-plan.md section 10 Environment Limitations
======================= 455 passed, 1 skipped in 5.70s ========================
```

NFR-3 target is 85% line coverage; measured TOTAL is 98% locally before and after the RO-2 deletion and 98% on Linux CI (human-supplied). No shortfall. NFR-1 measured by the perf test: best of 3 = 0.0174 s against the 1.0 s target (hard limit 2.0 s).

NFR-4 evidence (EC id in test names), count of `def test_ec_<n>_*` per EC from `grep -rhoiE "def test_ec_<n>_[a-z0-9_]*" tests | wc -l`:

```text
EC-1: 4
EC-2: 1
EC-3: 1
EC-4: 7
EC-5: 3
EC-6: 3
EC-7: 1
EC-8: 4
EC-9: 8
EC-10: 2
EC-11: 3
EC-12: 1
EC-13: 1
EC-14: 3
```

### 3.1 CI evidence (GitHub Actions)

`gh` is installed (2.97.0) but not logged in: `gh run list -R paggybansal/agentic-sdlc-docsync` printed `To get started with GitHub CLI, please run:  gh auth login` and `Alternatively, populate the GH_TOKEN environment variable with a GitHub API authentication token.` The repository is public, so the read-only REST API was queried unauthenticated with `curl` instead (no credential involved).

| Item | Value |
|---|---|
| Run | https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702 |
| Workflow, trigger | CI (`.github/workflows/ci.yml`), event `push`, branch `feature/DS-1-docsync`, run attempt 1, created 2026-10-09T10:32:22Z |
| Commit | `c8489911bfd284d8b5b13f67433c442e87d89602`, which is the commit verified in this report (`c848991`) |
| Run status | completed, conclusion `success` (the only run: `total_count: 1`) |

| Job | Conclusion | Steps (all `success`) |
|---|---|---|
| test (ubuntu-latest / py3.11) https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702/job/113779510686 | success | Install, Lint, Test with coverage, Documentation sync gate |
| test (ubuntu-latest / py3.12) https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702/job/113779510650 | success | Install, Lint, Test with coverage, Documentation sync gate |
| test (windows-latest / py3.11) https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702/job/113779510651 | success | Install, Lint, Test with coverage, Documentation sync gate |
| test (windows-latest / py3.12) https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702/job/113779510797 | success | Install, Lint, Test with coverage, Documentation sync gate |
| dependency audit (advisory) https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702/job/113779510319 | success | pip-audit |

The job logs could not be read by the verifier: `curl https://api.github.com/repos/paggybansal/agentic-sdlc-docsync/actions/jobs/113779510650/logs` returned `http=403` with the body `{"message": "Must have admin rights to Repository.", ...}`. On both Ubuntu jobs the step `Test with coverage` concluded `success`. The EL-1 and EL-2 closure below rests on figures the human read from the job log, not on anything the verifier measured. The `Documentation sync gate` step (`docsync generate` then `docsync check`) also passed on all four test jobs.

CI runs offline (FIX 1d). `.github/workflows/ci.yml` lines 38-40 run `docsync generate --repo . --out docs/PROJECT_DOCS.md` then `docsync check --repo . --out docs/PROJECT_DOCS.md`, with no `--github-repo` flag, and the workflow file sets no `DOCSYNC_GITHUB_TOKEN` (`grep -n DOCSYNC .github/workflows/ci.yml` printed nothing). With no repository named and no token the tool is offline (FR-9, FR-10, EC-5, EC-14), which is why the CI gate is consistent with the committed offline artifact `docs/PROJECT_DOCS.md` (commit `27b00d1`).

### 3.2 EL-1 and EL-2 evidence (status: CLOSED, human-supplied)

Attribution: the CI figures below are observations the human read from the job log and supplied to the verifier. The verifier did not measure them (the logs endpoint returned 403) and has not viewed the screenshot the human says shows the per-test log line; the screenshot is corroborating evidence held by the human. `pytest` runs verbosely in CI (`.github/workflows/ci.yml` line 35 is `run: python -m pytest -v --cov=src/docsync --cov-report=term-missing`, and `pyproject.toml` line 30 has `addopts = "-v --strict-markers"`).

| Item | Value |
|---|---|
| Run URL | https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702 |
| Job | `test (ubuntu-latest / py3.12)` (https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702/job/113779510650), step `Test with coverage` |
| Commit | `c8489911bfd284d8b5b13f67433c442e87d89602` (`git rev-parse c848991`) |
| Inference method | Pass/skip count differential: Linux py3.12 reported 456 passed and 0 skipped; the local Windows run reported 455 passed and 1 skipped. The one-test difference is the symlink test |

| Limitation | Test | Evidence (human-supplied) | Status |
|---|---|---|---|
| EL-1 | `tests/test_collect.py::test_scan_modules_symlinked_directory_is_not_followed` | 456 passed, 0 skipped on ubuntu-latest / py3.12 against 455 passed, 1 skipped on Windows local, so the symlink test executed and passed on Linux. The Windows skip is environmental: the manual attempt gave `OSError [WinError 1314] A required privilege is not held by the client`. Per-test log line: attached by the human as a screenshot (not viewed by the verifier) | CLOSED |
| EL-2 | `tests/test_integration.py::test_document_does_not_depend_on_file_creation_order` | The full suite ran on ubuntu-latest with zero failures, so this test ran on ext4 (not NTFS) and passed. The NTFS caveat no longer limits the evidence | CLOSED |

Residual weakness of the count-differential inference, recorded honestly while the status stays CLOSED as the human decided: the comparison is between different operating systems and Python versions (Linux 3.12 against Windows 3.14), so in principle another platform-dependent test could offset the symlink test in the counts. The collected total is 456 on both sides, and the only `skipif` in `tests/` is the symlink test (`grep -rn "skipif" tests` found it at `tests/test_collect.py:273`), which makes the inference reasonable. The EL-2 conclusion depends on the CI filesystem enumerating entries unsorted, which is typical of ext4 but was not itself measured.

## 4. Functional Verification Matrix

All commands were run from the repository root using the installed `docsync` entry point, with `DOCSYNC_GITHUB_TOKEN` unset unless stated.

| V-ID | Scenario | Expected | Actual | Exit code | Result |
|---|---|---|---|---|---|
| V-1 | Happy path, offline: `docsync generate --repo . --out docs/PROJECT_DOCS.md` | File written; exit 0 | stdout `wrote docs/PROJECT_DOCS.md`; the 7-section document in section 5 was produced | 0 | Pass |
| V-2 | Idempotency, file tracked (commit `27b00d1`): `docsync generate --repo . --out docs/PROJECT_DOCS.md` run twice, then `git diff --stat -- docs/PROJECT_DOCS.md`; byte compare as corroboration | 0 differing bytes; empty diff stat | PRIMARY evidence: after two generations `git diff --stat -- docs/PROJECT_DOCS.md` printed nothing between the markers `diff-stat-begin` and `diff-stat-end exit=0`, with the file tracked, so the empty output is meaningful. Corroboration: `cmp` against the first generation printed `byte-identical to first generation`; `git ls-files --eol docs/PROJECT_DOCS.md` printed `i/lf    w/lf    attr/text eol=lf`. Earlier (file untracked) the `cmp` of runs 1 and 3 was also identical and SHA-256 was `918b24b42d2438987b1621ac63d541e29b824d06f0feab21750b044fffbf828d`. The earlier untracked-file caveat no longer applies | 0 | Pass |
| V-3 | Sync check passes: `docsync check --repo . --out docs/PROJECT_DOCS.md` | `in sync`, exit 0 | `in sync` | 0 | Pass |
| V-4 | Drift: append a line to the generated file, run `check`, restore | exit 1 on drift | `drift detected: run "docsync generate" to update docs/PROJECT_DOCS.md`. File restored from a copy (`cmp` printed `restored`); `check` afterwards printed `in sync`, exit 0. Extra case (EC-12): `--out docs/NOPE.md` printed `drift detected: run "docsync generate" to update docs/NOPE.md`, exit 1, and the file was not created | 1 (drift); 0 (after restore); 1 (missing file) | Pass |
| V-5 | Empty repository: `docsync generate --repo <fresh mktemp dir> --out <dir>/docs/PROJECT_DOCS.md` | Complete 7-section document, unresolved fields `Not Found`, exit 0 | `wrote <tmp>/docs/PROJECT_DOCS.md`; 7 sections; every field is `Not Found` with one honest exception: the two Generation Info fields, Tool Version `0.1.0` and Schema Version `1`, always resolve because they come from the tool, not the repository (FR-5); `check` on that directory printed `in sync` | 0 | Pass |
| V-6 | Invalid input: `--repo ./does-not-exist`; also `--github-repo bad`; `--out x.txt` | Non-zero exit, one clear line, no traceback | `docsync: error: --repo is not an existing directory: './does-not-exist'`; `docsync: error: --github-repo must look like OWNER/NAME, got 'bad'`; `docsync: error: --out must end in .md, got 'x.txt'`; no traceback in any | 2, 2, 2 | Pass |
| V-7a | API failure, invalid token against the real API host (a made-up fake token value was exported for this one process and then unset): `docsync generate --repo <tmp> --github-repo octocat/Hello-World --verbose` | One warning, hosted fields `Not Found`, exit 0 | stderr: `docsync: DOCSYNC_GITHUB_TOKEN is set` then `warning: GitHub lookup failed: unexpected HTTP status 401; hosted fields are Not Found`; all six hosted rows `Not Found`; wall time 1.279 s; the token value appears nowhere in the output | 0 | Pass |
| V-7b | API unreachable: same command with `HTTPS_PROXY=http://127.0.0.1:9` (dead proxy; the API host is hard-coded so a proxy is how reachability was forced) | One warning, `Not Found`, exit 0 | `warning: GitHub lookup failed: request failed; hosted fields are Not Found`; wall time 2.583 s | 0 | Pass |
| V-8 | Secret safety: temp repo whose `pyproject.toml` description holds `ghp_A1b2C3d4E5f6G7h8I9j0K1L2` and `AKIAIOSFODNN7EXAMPLE` (fake shapes), `--verbose`, token exported | Redacted in the file and on the console | File row: `\| Description \| leak [REDACTED] and [REDACTED] end \|`; stdout and stderr contain none of `ghp_`, `AKIA`. Second run: the exported fake token's literal value placed in the description, `--offline --verbose`: file row `lit [REDACTED] end`; `grep -c "fake-literal"` over the file, stdout and stderr printed `0` for each; stderr said only `DOCSYNC_GITHUB_TOKEN is set` | 0 | Pass |
| V-9 (RO-5) | Generate docs/PROJECT_DOCS.md for this repository and assert it contains no `[REDACTED]` | 0 occurrences | `grep -c "REDACTED" docs/PROJECT_DOCS.md` printed `0` | 0 (generate) | Pass |
| V-10 (NFR-2, RO-8, changed by the human) | MANUAL one-off, unauthenticated, ONLINE flags, this repository's public metadata: token confirmed unset (`token-var: not set`), then `docsync generate --repo . --out docs/V10_TMP.md --github-repo paggybansal/agentic-sdlc-docsync --verbose` (a temporary output file, deleted afterwards so the committed document stays offline and deterministic) | Record duration, exit code, resolved vs `Not Found` fields | stderr: `docsync: DOCSYNC_GITHUB_TOKEN is not set`; `wrote docs/V10_TMP.md`; no warning. Wall time `real 0m0.834s`. All six hosted fields stayed `Not Found` (Full Name, Description, Default Branch, Visibility, License, Topics); 0 fields resolved. Cause, from the code: `src/docsync/github.py` `fetch()` returns all six fields `Not Found` with no request when the token is unset or blank (FR-9, EC-5), and the CLI has no flag that sends an unauthenticated request. The CLI therefore cannot perform an unauthenticated online lookup, so the NFR-2 online figure is `Not Found`. The remote is `https://github.com/paggybansal/agentic-sdlc-docsync.git` and the repository is public (the REST API answered 200 `"private": false`), so the limitation is the product's design, not the network. This is a one-off manual observation, not a repeatable test; the automated suite stays fully offline (NFR-7). The earlier offline run against an empty temporary repository (0.556 s, same result) is superseded by this one | 0 | Not Found (NFR-2 online figure); EC-5 demonstrated |
| V-10 side evidence, NOT the product | Labelled reference only: `curl -s https://api.github.com/repos/paggybansal/agentic-sdlc-docsync`, unauthenticated | Show what a lookup would return | `http=200 time=0.437647s`; `full_name = paggybansal/agentic-sdlc-docsync`, `description = None`, `default_branch = main`, `visibility = public`, `license = None`, `topics = []`. This times the GitHub API with curl, not `docsync`, so it is not an NFR-2 measurement | n/a (curl) | Info only |
| V-11 (NFR-2) | MANUAL, live, ONLINE, authenticated, run by the human; planned procedure in section 4.1; the verifier does not set, read or handle any token | Binding: exit code 0; at least full_name, default_branch and visibility resolved; the token appears nowhere in the output file or the console; a measured duration is produced. Hosted-field rule: Every hosted field that is non-null in the API response must resolve to a real value. Any field that is null in the API response renders Not Found, and that is CORRECT behaviour, not a defect. Record, per field, whether it resolved or stayed Not Found and why. | Pending - human to run | Pending - human to run | Pending - human to run |
| EL-1 manual (RO-9) | Create a directory symlink in a temp directory with `os.symlink(..., target_is_directory=True)` | Symlink created, or the refusal recorded | `OSError [WinError 1314] A required privilege is not held by the client` (paths in the message elided here). The shell is not elevated, so the skip is environmental. The "symlinked directories are not followed" scenario was not exercised | n/a | Limitation (environmental) |

### 4.1 V-11 planned procedure (manual, live, online, NFR-2): NOT YET RUN

Manual only. The automated suite stays offline, so NFR-7 is unaffected. The verifier has not run, set or handled any token for V-11.

| Step | Action |
|---|---|
| 1. Token | Create a fine-grained personal access token: public repositories read-only, no extra scopes, shortest available expiry |
| 2. Session | PowerShell, token set for this shell session only with `Read-Host` into `$env:DOCSYNC_GITHUB_TOKEN`; never typed on a command line, never in shell history, `.env` or any file |
| 3. Command | `docsync generate --repo . --github-repo paggybansal/agentic-sdlc-docsync --out $env:TEMP\v11-online.md --verbose`; the output goes OUTSIDE `docs/` so the committed document is not touched |
| 4. Timing | Three runs, each wrapped in `Measure-Command`; the best (minimum) wall-clock duration is the NFR-2 online figure (target < 5 s) |
| 5. Teardown | `Remove-Item Env:DOCSYNC_GITHUB_TOKEN`; close the shell; revoke the token on GitHub and record the revocation; delete `$env:TEMP\v11-online.md`; confirm `git status --short` is unaffected |

Binding assertions (V-11 fails if any of these fails):

| Assertion | Expected | Actual | Result |
|---|---|---|---|
| Exit code | 0 | Pending - human to run | Pending - human to run |
| `full_name`, `default_branch`, `visibility` resolved | all three resolved to real values | Pending - human to run | Pending - human to run |
| Token string absent from the temp file | 0 occurrences | Pending - human to run | Pending - human to run |
| Token string absent from captured console output | 0 occurrences | Pending - human to run | Pending - human to run |
| A measured duration is produced (best wall-clock of 3 runs; target < 5 s) | a figure | Pending - human to run | Pending - human to run |

Hosted-field rule (verbatim): Every hosted field that is non-null in the API response must resolve to a real value. Any field that is null in the API response renders Not Found, and that is CORRECT behaviour, not a defect. Record, per field, whether it resolved or stayed Not Found and why.

Recorded items (non-binding; record the outcome, do not fail V-11 on them):

| Item | Expected | Actual | Result |
|---|---|---|---|
| No `[REDACTED]` in the hosted fields | 0 occurrences | Pending - human to run | Pending - human to run |
| Token revoked on GitHub (recorded) | revoked | Pending - human to run | Pending - human to run |
| `Remove-Item Env:DOCSYNC_GITHUB_TOKEN` done and shell closed | done | Pending - human to run | Pending - human to run |
| Temp file deleted, repo tree unaffected | yes | Pending - human to run | Pending - human to run |

Per-field recording table:

| Hosted field | Non-null in the API response? | Resolved or Not Found | Why |
|---|---|---|---|
| Full Name (`full_name`) | Pending - human to run | Pending - human to run | Pending - human to run |
| Description (`description`) | Pending - human to run | Pending - human to run | Pending - human to run |
| Default Branch (`default_branch`) | Pending - human to run | Pending - human to run | Pending - human to run |
| Visibility (`visibility`) | Pending - human to run | Pending - human to run | Pending - human to run |
| License (`license`) | Pending - human to run | Pending - human to run | Pending - human to run |
| Topics (`topics`) | Pending - human to run | Pending - human to run | Pending - human to run |

Chore note (no task id): the repository description, topics and an MIT LICENSE were populated on GitHub BEFORE V-11, specifically so that all six hosted fields are non-null and the online path is fully exercised. The `LICENSE` file was added to the repository as commit `91fdad9` (`chore: add MIT LICENSE`). The earlier curl reference (V-10 side evidence) showed `description` and `license` as `None` BEFORE this population; that observation is superseded for V-11 and V-11 must be judged by its own per-field table.


## 5. Output Document Quality Check

Document checked: `docs/PROJECT_DOCS.md` as generated by V-1 (66 lines). After the RO-2 deletion it was regenerated and now has 65 lines (`wc -l`), 45 table lines (re-measured with a Python count), SHA-256 `42f2fc700ad959c84e5adeb91d8ddf4299a200113dde0fdd639f43c41b4abced`, and 8 `Not Found` fields (unchanged); the other checks in this table were not re-run on the regenerated file, whose only change is one deleted module row.

| Check | Expected | Actual | Result |
|---|---|---|---|
| All required sections (FR-2) present, in order | Project Overview, Identity & Metadata, Hosted Repository Metadata, Modules & Entry Points, Dependencies, Test Suite Summary, Generation Info | `grep -n "^#"`: lines 1, 8, 17, 28, 44, 54, 61 hold exactly those seven `##` headings in that order | Pass |
| At least one field rendered `Not Found` | 1 or more | 8 occurrences: Identity License and Authors, all six Hosted Repository Metadata fields | Pass |
| No secret-shaped strings | none of `sk-`, `ghp_`, `github_pat`, `AKIA` | `grep -nE "sk-\|ghp_\|github_pat\|AKIA"` printed nothing (exit 1) | Pass |
| No placeholder text | none of `TODO`, `TBD`, `lorem` (case-insensitive) | `grep -niE` printed nothing (exit 1) | Pass |
| No `[REDACTED]` (V-9) | 0 | 0 | Pass |
| Valid Markdown: headings | headings nest correctly | seven `##` headings, no skipped level, no `#` title (the architecture fixes the document as 7 sections) | Pass |
| Valid Markdown: tables | every table well formed | 46 table lines at V-1 (45 after the RO-2 regeneration), each with exactly 3 pipe characters (2 columns); each table has a header row and a `\|---\|---\|` separator | Pass |
| Line endings and ending (FR-17) | LF only, exactly one trailing newline | `tail -c 16 docs/PROJECT_DOCS.md \| xxd` printed `00000000: 6120 5665 7273 696f 6e20 7c20 3120 7c0a  a Version \| 1 \|.` (one `0a`, preceded by `7c`, not `0a0a`); a Python check on the raw bytes printed `ends with single LF: True CR count 0` | Pass |
| No timestamp or commit hash | none | `grep -ciE "[0-9]{4}-[0-9]{2}-[0-9]{2}\|\b[0-9a-f]{7,40}\b\|timestamp\|commit"` printed `0` | Pass |
| Still in sync after the V-10 run | `check` exit 0 | `in sync`, exit 0; `docs/V10_TMP.md` was deleted (`ls` reported no such file) | Pass |
| No volatile values (FR-5) | Generation Info has only tool and schema versions | `Tool Version 0.1.0`, `Schema Version 1`; no timestamp, no hash | Pass |

Content note (not a defect): `Test Functions | 262` is a static count of `test_*` functions in 8 test files; pytest collected 456 items because of parametrisation. The two numbers measure different things (architecture decision: static derivation, nothing is executed).

## 6. Requirement Verification Summary

Verified by the full suite run in section 3 (455 passed, 1 skipped) and the matrix in docs/05-code-review.md section 4, plus the commands in section 4 above. "Test" means a passing automated test; names are in docs/05-code-review.md section 4 and were not re-listed here. Evidence for the FR/EC rows below is the pytest run unless a V-ID is named.

| FR/NFR/EC ID | Verified by | Result |
|---|---|---|
| FR-1, FR-18 | Tests in `tests/test_cli.py`; V-1 (default `--out` under `--repo`); V-6 (`--out x.txt` rejected) | Pass |
| FR-2 | `tests/test_render.py::test_document_has_seven_sections_in_order`; section 5 | Pass |
| FR-3, FR-14 | Tests; V-5; section 5 (8 `Not Found` fields) | Pass |
| FR-4, FR-5 | Tests; section 5 (Hosted block has six fields; Generation Info has two) | Pass |
| FR-6, FR-7, FR-8, FR-20 | Tests; V-8 (file, stdout and stderr clean; only `is set` logged) | Pass |
| FR-9, FR-10 | Tests; V-10 (token unset gives no request even with `--github-repo`) | Pass |
| FR-11, FR-12 | Tests; V-7a and V-7b (one warning, `Not Found`, exit 0) | Pass |
| FR-13 | Tests; V-5 | Pass |
| FR-15, FR-16 | Tests; V-3, V-4 | Pass |
| FR-17 | Tests; V-2 | Pass |
| FR-19 | Tests; V-6 (exit 2, no traceback) | Pass |
| NFR-1 | `tests/test_perf.py::test_offline_under_1s`: 0.0174 s (target 1.0 s, hard 2.0 s) | Pass |
| NFR-2 | Offline figure kept: `tests/test_perf.py::test_offline_under_1s` best of 3 = 0.0174 s (target 1.0 s). Mocked timeout test passes; V-7b measured 2.583 s and V-7a 1.279 s for failed lookups only. Online figure: `Pending V-11` (to be replaced by the measured best duration). Corroborating side evidence only, not the product: `curl` to the public API returned HTTP 200 in 0.437647 s (V-10) | Partially verified (online pending V-11) |
| NFR-3 | 98% total locally (re-measured after the RO-2 deletion) and 98% on Linux CI (human-supplied) against the 85% target | Pass |
| NFR-4 | EC grep in section 3: every EC-1..EC-14 has at least one test name containing its id | Pass |
| NFR-5 | `pip list` shows `requests` as the only runtime dependency of `docsync`; `pyproject.toml` runtime list in the generated document: `requests>=2.32.0` | Pass |
| NFR-6 | `ruff check .`: `All checks passed!` | Pass |
| NFR-7 | Autouse fixture in `tests/conftest.py`; suite passed; the manual runs V-7a, V-7b, V-10 were outside the suite | Pass |
| NFR-8 | V-2 | Pass |
| NFR-9 | V-3, V-4, V-6 exit codes 0, 1, 2 only; no prompts occurred in any run | Pass |
| NFR-10 | V-8, V-9, section 5 secret scan; known residuals CR-38 and others in section 8 | Pass with limitations |
| EC-1..EC-4 | Tests named `test_ec_1_*` to `test_ec_4_*`; V-7a (401 path) and V-7b (connection failure) | Pass |
| EC-5 | Tests; V-1 and V-10 | Pass |
| EC-6 | Tests; V-5 | Pass |
| EC-7, EC-8, EC-13 | Tests (EC-8 symlink case aside, see EL-1) | Pass |
| EC-9 | Tests; V-8 | Pass |
| EC-10, EC-11 | Tests; V-6 | Pass |
| EC-12 | Tests; V-4 (missing file gave exit 1, file not created) | Pass |
| EC-14 | Tests; V-1 (no `--github-repo`, hosted fields `Not Found`) | Pass |

## 7. Defects Found

None.

No High-severity, security-false-negative or accepted-AC defect was found, so the triage rule (RO-11) did not stop this step. No new CR ids were created. V-9 found no `[REDACTED]`, so nothing was escalated. Observations that are disclosed limitations and not defects: `__main__.py` at 0% line coverage (CR-10), the NFR-2 online figure `Pending V-11`, EL-1 and EL-2 `Open (pending log evidence)`.

## 8. Known Limitations

### 8.1 Fields that legitimately render `Not Found`

| Where | Field | Why |
|---|---|---|
| docs/PROJECT_DOCS.md, Identity & Metadata | License | This repository's `pyproject.toml` declares no license. Adding a `LICENSE` file (commit `91fdad9`) did not change this: the tool reads only `pyproject.toml` (FR-7, `test_collect_pyproject_opens_only_pyproject`), so the field stays `Not Found`; regenerating produced an empty `git diff` |
| docs/PROJECT_DOCS.md, Identity & Metadata | Authors | This repository's `pyproject.toml` declares no authors |
| docs/PROJECT_DOCS.md, Hosted Repository Metadata | Full Name, Description, Default Branch, Visibility, License, Topics | Offline mode: no token and no `--github-repo` supplied, so no request is made (FR-9, EC-5, EC-14) |
| NFR-2 | Online wall-clock time of a successful lookup | `Pending V-11`: not observable without a token (FR-9, EC-5; V-10 showed this); the human's manual authenticated run V-11 will supply the figure. Until then it is `Not Found` |
| docs/04-impl-plan.md | Estimates of T20, T21, T22 | `Not Found` permanently by human decision (RO-7); step 8 discloses it as a process limitation |
| EL-1, EL-2 | Per-test result of the symlink test and the directory-order test on Linux CI | Closed by human-supplied CI evidence (section 3.2); no longer `Not Found` |

### 8.2 Environment limitations (EL-1 to EL-3; EL-1 and EL-2 closed) and manual evidence (RO-9, RO-10)

EL-4 (line endings) is disclosed in section 1, as docs/04 section 10 requires, and is not repeated as a limitation.

| ID | Limitation | Evidence from this step |
|---|---|---|
| EL-1 | CLOSED (human-supplied CI evidence). Directory symlinks cannot be created on the Windows development machine, so `test_scan_modules_symlinked_directory_is_not_followed` is skipped there | Windows manual attempt: `OSError [WinError 1314] A required privilege is not held by the client` (paths omitted); environmental. Linux: ubuntu-latest / py3.12 reported 456 passed, 0 skipped against 455 passed, 1 skipped locally, so the test executed and passed on Linux (section 3.2) |
| EL-2 | CLOSED (human-supplied CI evidence). The directory-creation-order determinism test cannot fail on NTFS | The full suite ran on ubuntu-latest (ext4) with zero failures, so `test_document_does_not_depend_on_file_creation_order` ran and passed there (section 3.2). Ordering is also covered directly by `test_scan_modules_output_sorted_by_code_point` |
| EL-3 | No automated test exercises the live GitHub API, by design (NFR-7) | V-7a and V-7b exercised failure paths manually; V-10 showed an unauthenticated online lookup is impossible (FR-9, EC-5); a successful online lookup was not observed; V-11 is the planned manual closure (section 4.1) |
| RO-10 | Dependency floor | Only the installed dependency versions were audited: requests 2.34.2, urllib3 2.8.0, certifi 2026.7.22, idna 3.20, charset-normalizer 3.5.2 (plus pytest 9.1.1, pytest-cov 7.1.0, ruff 0.16.10 and their dependencies). The declared lower bound requests>=2.32.0 was not independently audited; a consumer resolving to the floor version is outside the verified configuration. The local editable package `docsync (0.1.0)` is out of scope for a vulnerability database lookup |

### 8.3 Deferred findings from docs/05-code-review.md (verbatim from sections 7.7.2, 7.10 and 7.11, CR-33 excluded per 7.7.3)

Status for every row: Deferred, disclosed as Known Limitation. CR-9 update: the empty `collectors/` stub was removed in commit `bbc142c` (RO-2); the row below is reproduced verbatim as recorded, and the part about `CollectError` and `GitHubError` never being raised still stands. CR-42 is the highest id in docs/05-code-review.md plus one (the highest there is CR-41, checked with grep); it is recorded here only, and docs/05-code-review.md was NOT edited, because step 6 is closed, that review document is the code-reviewer's artifact, and the verifier's rule is to disclose and not remediate. The step 8 pull-request description must carry it, and the human may ask for a row in docs/05 later.

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

### 8.4 Other limitations observed in this step

| Item | Detail |
|---|---|
| Static test counts | The Test Suite Summary counts `test_*` functions statically (262) and does not equal pytest's collected item count (456) |
| `check` for CI | Not run in a CI environment in this session; the CI run in section 3.1 ran `generate` then `check` offline and passed |
| Committed artifact is offline (FIX 1c) | The committed docs/PROJECT_DOCS.md is the offline rendering. An authenticated run resolves the six hosted fields and therefore reports drift against the committed offline artifact. Both CI and the committed artifact use offline mode; mixing modes between generate and check is a configuration error, not a tool defect. |

## 9. Verification Verdict

**Pass with limitations.**

This verdict is CONDITIONAL only on V-11 being run and recorded by the human (section 4.1); EL-1 and EL-2 are closed (section 3.2). Basis: ruff 0 findings; the CI run on the same commit succeeded on all five jobs (section 3.1); 455 passed and 1 skipped locally and 456 passed, 0 skipped on Linux CI (human-supplied); coverage 98% against an 85% target; pip-audit clean for installed dependencies; V-1 to V-9 passed; the generated document passed all quality checks; no defects found (section 7). Limitations are those in section 8: the NFR-2 online figure for a successful lookup is `Pending V-11`, the declared dependency floor was not audited (RO-10), and the deferred findings are disclosed.

Clean-tree statement: during step 7 these commits were made, each containing only its own files: `27b00d1` (`docs/PROJECT_DOCS.md`), `91fdad9` (`LICENSE`), `bbc142c` (deletion of `src/docsync/collectors/__init__.py`, authorised by the human as RO-2 completion), `0c334f2` (`docs/PROJECT_DOCS.md`); `9a84131` was committed by the human. The file modified for V-4 was restored (`cmp` printed `restored`; `check` returned `in sync`). `docs/06-verification.md` has uncommitted edits made after `9a84131`, and the six pre-existing files under `evidence/` (`step-00-gitlog.txt`, `step-00-tree.txt`, `step-01-gitlog.txt`, `step-02-architecture.txt`, `till_step5.txt`, `till_step6.txt`) remain untracked. Apart from the `src/docsync/collectors/` deletion, `src/` and `tests/` were not touched.

---
**Gate:** Approve step 7 and continue? (yes / changes needed)
