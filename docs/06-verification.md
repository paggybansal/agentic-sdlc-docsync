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
| Commit hash | `c848991` (`git rev-parse --short HEAD`), branch `feature/DS-1-docsync` |
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

Skip reason (`python -m pytest -q -rs`, filtered with `grep -i skip`):

```text
SKIPPED [1] tests\test_collect.py:273: EL-1: directory symlink creation is not permitted in this environment (Windows needs elevated privileges or Developer Mode); see docs/04-impl-plan.md section 10 Environment Limitations
======================= 455 passed, 1 skipped in 5.70s ========================
```

NFR-3 target is 85% line coverage; measured TOTAL is 98%. No shortfall. NFR-1 measured by the perf test: best of 3 = 0.0174 s against the 1.0 s target (hard limit 2.0 s).

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

Symlink test on Linux (EL-1) and directory-order test (EL-2): `Not Found`. The per-test lines are in the job logs, and the logs endpoint refused the request: `curl https://api.github.com/repos/paggybansal/agentic-sdlc-docsync/actions/jobs/113779510650/logs` returned `http=403` with the body `{"message": "Must have admin rights to Repository.", ...}`. What the evidence does show: on both Ubuntu jobs the step `Test with coverage` (`python -m pytest -v --cov=src/docsync --cov-report=term-missing`) concluded `success`, so pytest exited 0 there. The symlink test is guarded only by `skipif(not _symlinks_available())` (`tests/test_collect.py:273`), so on Linux it either passed or skipped; the job conclusion alone cannot tell which, and I do not claim it executed. EL-1 and EL-2 are therefore NOT closed by evidence available to this step. A person with log access can read the `test_scan_modules_symlinked_directory_is_not_followed` line in the Ubuntu job logs to close EL-1. The `Documentation sync gate` step (`docsync generate` then `docsync check`) also passed on all four test jobs.

CI runs offline (FIX 1d). `.github/workflows/ci.yml` lines 38-40 run `docsync generate --repo . --out docs/PROJECT_DOCS.md` then `docsync check --repo . --out docs/PROJECT_DOCS.md`, with no `--github-repo` flag, and the workflow file sets no `DOCSYNC_GITHUB_TOKEN` (`grep -n DOCSYNC .github/workflows/ci.yml` printed nothing). With no repository named and no token the tool is offline (FR-9, FR-10, EC-5, EC-14), which is why the CI gate is consistent with the committed offline artifact `docs/PROJECT_DOCS.md` (commit `27b00d1`).

### 3.2 EL-1 and EL-2 log evidence (status: Open (pending log evidence))

The job logs are readable only with repository admin rights (HTTP 403 for the verifier). The human is asked to paste the exact lines. `pytest` runs verbosely in CI: `.github/workflows/ci.yml` line 35 is `run: python -m pytest -v --cov=src/docsync --cov-report=term-missing`, and `pyproject.toml` line 30 has `addopts = "-v --strict-markers"`, so each test prints a `PASSED` or `SKIPPED` line.

| Item | Value |
|---|---|
| Run URL | https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702 |
| Job | `test (ubuntu-latest / py3.12)` (https://github.com/paggybansal/agentic-sdlc-docsync/actions/runs/37918218702/job/113779510650), step `Test with coverage` |
| Inference rule | `PASSED` on Linux closes the limitation. `SKIPPED` means it did not close and the limitation stands |

| Limitation | Test | Exact log line | Status |
|---|---|---|---|
| EL-1 | `tests/test_collect.py::test_scan_modules_symlinked_directory_is_not_followed` | Pending - human to paste | Open (pending log evidence) |
| EL-2 | `tests/test_integration.py::test_document_does_not_depend_on_file_creation_order` | Pending - human to paste | Open (pending log evidence) |


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

Document checked: `docs/PROJECT_DOCS.md` (66 lines, generated by V-1).

| Check | Expected | Actual | Result |
|---|---|---|---|
| All required sections (FR-2) present, in order | Project Overview, Identity & Metadata, Hosted Repository Metadata, Modules & Entry Points, Dependencies, Test Suite Summary, Generation Info | `grep -n "^#"`: lines 1, 8, 17, 28, 44, 54, 61 hold exactly those seven `##` headings in that order | Pass |
| At least one field rendered `Not Found` | 1 or more | 8 occurrences: Identity License and Authors, all six Hosted Repository Metadata fields | Pass |
| No secret-shaped strings | none of `sk-`, `ghp_`, `github_pat`, `AKIA` | `grep -nE "sk-\|ghp_\|github_pat\|AKIA"` printed nothing (exit 1) | Pass |
| No placeholder text | none of `TODO`, `TBD`, `lorem` (case-insensitive) | `grep -niE` printed nothing (exit 1) | Pass |
| No `[REDACTED]` (V-9) | 0 | 0 | Pass |
| Valid Markdown: headings | headings nest correctly | seven `##` headings, no skipped level, no `#` title (the architecture fixes the document as 7 sections) | Pass |
| Valid Markdown: tables | every table well formed | 46 table lines, each with exactly 3 pipe characters (2 columns); each table has a header row and a `\|---\|---\|` separator | Pass |
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
| NFR-3 | 98% total against 85% target | Pass |
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
| EL-1, EL-2 | Per-test result of the symlink test and the directory-order test on Linux CI | `Pending - human to paste` (section 3.2); the logs returned HTTP 403 to the verifier. Status `Open (pending log evidence)` |

### 8.2 Environment limitations (EL-1 to EL-3) and manual evidence (RO-9, RO-10)

EL-4 (line endings) is disclosed in section 1, as docs/04 section 10 requires, and is not repeated as a limitation.

| ID | Limitation | Evidence from this step |
|---|---|---|
| EL-1 | Directory symlinks cannot be created on the development machine, so `test_scan_modules_symlinked_directory_is_not_followed` is skipped; "symlinked directories are not followed" is implemented but not exercised by a passing test here | Windows manual attempt: `OSError [WinError 1314] A required privilege is not held by the client` (the paths in the message are omitted here); the shell is not elevated, so the skip is environmental. Linux: both Ubuntu CI jobs passed pytest (section 3.1), but the symlink test's own line is not yet seen (logs HTTP 403). Status: Open (pending log evidence); see section 3.2 |
| EL-2 | The directory-creation-order determinism test cannot fail on NTFS, which enumerates entries sorted | Status: Open (pending log evidence); the Ubuntu jobs passed, but the test's own result line is not yet seen (section 3.2). Ordering is covered directly by `test_scan_modules_output_sorted_by_code_point` |
| EL-3 | No automated test exercises the live GitHub API, by design (NFR-7) | V-7a and V-7b exercised failure paths manually; V-10 showed an unauthenticated online lookup is impossible (FR-9, EC-5); a successful online lookup was not observed; V-11 is the planned manual closure (section 4.1) |
| RO-10 | Dependency floor | Only the installed dependency versions were audited: requests 2.34.2, urllib3 2.8.0, certifi 2026.7.22, idna 3.20, charset-normalizer 3.5.2 (plus pytest 9.1.1, pytest-cov 7.1.0, ruff 0.16.10 and their dependencies). The declared lower bound requests>=2.32.0 was not independently audited; a consumer resolving to the floor version is outside the verified configuration. The local editable package `docsync (0.1.0)` is out of scope for a vulnerability database lookup |

### 8.3 Deferred findings from docs/05-code-review.md (verbatim from sections 7.7.2, 7.10 and 7.11, CR-33 excluded per 7.7.3)

Status for every row: Deferred, disclosed as Known Limitation. CR-42 is the highest id in docs/05-code-review.md plus one (the highest there is CR-41, checked with grep); it is recorded here only, and docs/05-code-review.md was NOT edited, because step 6 is closed, that review document is the code-reviewer's artifact, and the verifier's rule is to disclose and not remediate. The step 8 pull-request description must carry it, and the human may ask for a row in docs/05 later.

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

### 8.4 Other limitations observed in this step

| Item | Detail |
|---|---|
| Static test counts | The Test Suite Summary counts `test_*` functions statically (262) and does not equal pytest's collected item count (456) |
| `check` for CI | Not run in a CI environment in this session; the CI run in section 3.1 ran `generate` then `check` offline and passed |
| Committed artifact is offline (FIX 1c) | The committed docs/PROJECT_DOCS.md is the offline rendering. An authenticated run resolves the six hosted fields and therefore reports drift against the committed offline artifact. Both CI and the committed artifact use offline mode; mixing modes between generate and check is a configuration error, not a tool defect. |

## 9. Verification Verdict

**Pass with limitations.**

This verdict is CONDITIONAL on the human recording V-11 (section 4.1) and the EL-1 and EL-2 log lines (section 3.2); until then those items read `Pending`. Basis: ruff 0 findings; the CI run on the same commit succeeded on all five jobs (section 3.1); 455 passed and 1 skipped (EL-1); coverage 98% against an 85% target; pip-audit clean for installed dependencies; V-1 to V-9 passed; the generated document passed all quality checks; no defects found (section 7). Limitations are those in section 8: the NFR-2 online figure for a successful lookup is `Not Found` (V-10: impossible unauthenticated by design), EL-1 to EL-3 are not closed by CI evidence (logs not readable), the declared dependency floor was not audited (RO-10), and the deferred redactor findings are disclosed.

Clean-tree statement: `LICENSE` was committed alone as `91fdad9` (`chore: add MIT LICENSE`) and `docs/PROJECT_DOCS.md` alone as `27b00d1` (`docs(step-7): track offline-rendered PROJECT_DOCS.md`, authorised by the human); `docs/06-verification.md` is created and uncommitted. The file modified for V-4 was restored (`cmp` printed `restored`; `check` returned `in sync`). `git status --short` shows only `docs/06-verification.md` plus the six pre-existing untracked files under `evidence/` (`step-00-gitlog.txt`, `step-00-tree.txt`, `step-01-gitlog.txt`, `step-02-architecture.txt`, `till_step5.txt`, `till_step6.txt`), which were left in place. No tracked file was modified (`git diff --stat` printed nothing). `src/` and `tests/` were not touched.

---
**Gate:** Approve step 7 and continue? (yes / changes needed)
