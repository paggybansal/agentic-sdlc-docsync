# Code Review — DS-1 Automated Documentation Sync

| Field | Value |
|---|---|
| Artifact | docs/05-code-review.md |
| SDLC Step | 6 — Code Review |
| Source documents | docs/01-requirements.md, docs/02-architecture.md, docs/03-design-review.md, docs/04-impl-plan.md (Sections 9 and 10: RO-1, EL-1..EL-3), src/docsync/, tests/ |
| Author | code-reviewer |
| Date | 2026-10-07 |
| Status | Draft |

## 1. Review Metadata

| Item | Value |
|---|---|
| Reviewed commit | 18aa32b (`git rev-parse --short HEAD`), branch feature/DS-1-docsync |
| Product files reviewed | 10 Python files under src/docsync/ (`__init__`, `__main__`, `cli`, `collect`, `collectors/__init__`, `errors`, `github`, `model`, `redact`, `render`) |
| Test files reviewed | 9 Python files under tests/ (`conftest`, `test_cli`, `test_collect`, `test_github`, `test_integration`, `test_model`, `test_perf`, `test_redact`, `test_render`) |
| LOC (`wc -l`) | src/docsync/*.py: 592 total (cli 147, collect 157, github 96, render 107, redact 35, model 23, errors 17, `__main__` 8, `__init__` 2, `collectors/__init__` 0). tests/*.py: 3048 total (test_cli 987, test_collect 498, test_github 468, test_render 391, test_integration 282, test_redact 210, test_perf 119, test_model 79, conftest 14) |
| Test run | 298 collected, 297 passed, 1 skipped (EL-1 symlink test) |
| Environment | Python 3.14.2, pytest 9.1.1, Windows 11; requests 2.34.2, urllib3 2.8.0 (from `pip list`) |
| Out of scope for review | The working tree also holds pre-existing uncommitted pipeline files (`.claude/*`, `CLAUDE.md`, `.env.example`, `evidence/*`). They are not product code and were neither reviewed nor touched. |
| Method | Every file in src/docsync/ and tests/ read; the five mandated commands run in this session (Section 5); additional probes written under a temp directory outside the repository (redaction behaviour, ReDoS timing, `--out` / `--github-repo` validation, end-to-end false positives). No repository file other than this report was changed. |

## 2. Mandatory Review Areas

| Area | Review question | Verdict | Evidence | Action |
|---|---|---|---|---|
| Correctness | Does each component behave as specified in `01-requirements.md`? | Pass with comment | All FR-1..FR-20 and EC-1..EC-14 are implemented and have passing tests (Section 4); 297 passed, 1 skipped (Section 5, cmd 1). Defects: redaction false positives corrupt legitimate content, e.g. entry point `keygen = [REDACTED]` and dependency `keyring=[REDACTED]` (`src/docsync/redact.py:14-18`, CR-3); an undecodable test file is reported as a "syntax error" (`src/docsync/collect.py:129-130`, CR-8); default `--out` is rejected when cwd is outside `--repo` (`src/docsync/cli.py:60-65`, CR-4) | Fix CR-3 and CR-8; decide CR-4 and update docs |
| Security | Are secrets excluded from output? Is user input validated? | Fail | Positive: every print goes through `_emit` (`cli.py:79-81`), the document through `redact` (`cli.py:95`), the token is only read at `cli.py:100,122`, the only host is `github.py:11`; `--out` and `--github-repo` validation resisted every bypass tried (Section 3, CR-12 for the residual gaps). Negative: `redact()` has quadratic and cubic regex backtracking, so a 20,003-char word takes 5.2 s in `_URL_USERINFO` and a 20,001-char `a-a-...=` string takes 26.5 s in `_KEY_VALUE` (`redact.py:13-18`, CR-1); secret shapes named in the repo's own scan and skill are not redacted: `AKIAIOSFODNN7EXAMPLE`, `sk-ant-api03-abcdef`, PEM private key blocks, and `key = "unterminated` pass through unchanged (probe output in CR-2) | Fix CR-1 and CR-2 before approval |
| Error Handling | Are all API failures, missing files and empty repos handled gracefully? | Pass with comment | API: timeout, `RequestException`, non-2xx, bad JSON, non-object JSON all give one fixed-text warning (`github.py:30-47,94-95`; tests `test_ec_1_*` to `test_ec_4_*`). Missing/malformed/unreadable `pyproject.toml` (`collect.py:58-65`), empty repo (`test_ec_6_empty_repo_returns_complete_default_facts`), write failure (`test_write_failure_at_out_exits_2_without_traceback`), KeyboardInterrupt and BrokenPipe (`cli.py:137-140`) are handled. Gaps: `collect.py:131-132` (OSError reading a test file) never executed in the coverage run; wrong warning wording for undecodable files (CR-8). `except Exception` at `cli.py:145` is acceptable (CR-13) | Address CR-8; add a test for `collect.py:131-132` (CR-10) |
| Test Coverage | Do tests cover the happy path **and** the `Not Found` / missing-field edge cases? | Pass with comment | 97% total, 100% on cli, github, redact, render, model, errors; misses `collect.py:111->108, 131-132` and `__main__.py` 0% (Section 5, cmd 2). Not Found paths are tested: `test_ec_4_single_missing_key_gives_only_that_field_not_found`, `test_ec_4_wrong_typed_string_field_gives_not_found_without_warning`, `test_ec_7_missing_pyproject_is_not_found_without_warning`, `test_missing_dict_keys_render_not_found`, `test_ec_14_*`. All 14 ECs have a test whose name contains the EC id (NFR-4). No test for ReDoS, false positives, AKIA/sk-ant/PEM, or the unterminated-quote case; two tests exercise only a test double (CR-10) | Add tests with the CR-1/CR-2/CR-3 fixes; strengthen the weak tests in CR-10 |
| Code Clarity | Are function names self-explanatory? Is logic followable without comments? | Pass | Small single-purpose functions with docstrings: `parse_args`, `_check_out`, `_document`, `_run`, `_fail`, `collect_pyproject`, `scan_modules`, `_summarise_tests`, `fetch`, `_get_payload`, `normalise`, `redact`. The longest function is `collect_pyproject` (31 lines, `collect.py:54-84`), within the plan's ~40 lines per task guideline. The only comment on logic is the justified `# noqa: BLE001` (`cli.py:145`). `test_cli.py` is 987 lines (CR-15) | None blocking |
| DRY Principle | Is there duplicated logic that should be a shared function? | Pass with comment | `_text` is byte-identical in `collect.py:30-31` and `github.py:50-51`; both modules also have a `_license` that does `_text(...)` plus a type check (`collect.py:43-44`, `github.py:54-56`); `_strings` (`collect.py:34-36`) and `_topics` (`github.py:59-62`) are the same "list of non-empty strings, sorted" idea; `redact(..., secrets=(token or "",))` is written twice (`cli.py:81,95`) and `DOCSYNC_GITHUB_TOKEN` is read in two places (`cli.py:100,122`). Redaction itself is one shared function, as required (FR-6) | CR-7 (non-blocking) |
| Dependency Safety | Any known-vulnerable package versions? | Pass | `python -m pip_audit` returned `No known vulnerabilities found` (exit 0; Section 5, cmd 4). Runtime dependency is only `requests>=2.32.0` (`pyproject.toml`); installed requests 2.34.2, urllib3 2.8.0, certifi 2026.7.22, idna 3.20, charset-normalizer 3.5.2. pip-audit skipped the project itself (`docsync (0.1.0)` not on PyPI), which is expected. Not Found: whether the declared floor `requests>=2.32.0` itself has known advisories (only installed versions were audited) | None |

## 3. Findings

Severity scale: Blocker | Major | Minor | Info. Blocking findings are CR-1 and CR-2.

| ID | Severity | File:line | Issue | Recommendation |
|---|---|---|---|---|
| CR-1 | Major | src/docsync/redact.py:13-18 | Catastrophic backtracking (ReDoS) in the shared redactor. Measured by running each pattern's `.sub` on crafted input: `_URL_USERINFO` is quadratic on any long run of `[\w]` characters without `@` (5,003 chars 0.34 s; 10,003 chars 1.38 s; 20,003 chars 5.25 s; `"a"*20000+"://"` 3.0 s). `_KEY_VALUE` is worse on `"a-"*n + "="` (5,001 chars 1.24 s; 10,001 chars 5.05 s; 20,001 chars 26.5 s) because `[\w.-]*` before `key` and the `\b` start allow a scan from every offset. `redact()` runs over the whole rendered document and over every error message that echoes `--out`/`--repo`, and `docsync check` is designed for CI, so a pull request that adds one long description or path can stall the job (NFR-1, NFR-9, NFR-10) | Anchor and bound the patterns: restrict the scheme to `[a-z][a-z0-9+.-]{0,31}://` and the userinfo to a bounded length; use `\b(?<![\w.-])` plus a bounded key prefix (`[\w.-]{0,64}`) in `_KEY_VALUE`, or tokenise instead of regex-scan. Add a regression test that redacts a 100,000-char hostile string in under a second |
| CR-2 | Major | src/docsync/redact.py:8-18 | Coverage gaps in the redaction rules. Probe results (`redact()` output equals input for all of these): `AKIAIOSFODNN7EXAMPLE`, `sk-ant-api03-abcdef`, `-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----`, `git+https://tok@github.com/o/r.git` (userinfo without a colon), `API key is abc123def`, and `key = "unterminated` (a leading quote with no closing quote is not matched by the value alternatives at lines 15-16, so the value leaks). The tool's own secret scan and `.claude/skills/secret-safety/SKILL.md` list sk-, AKIA, xox, JWT and PEM as patterns that must be replaced; docs/02-architecture.md Section on Redaction lists a narrower set, so the implementation matches the architecture but not the skill or NFR-10 ("secret-looking values") | Human decision needed: either add the skill's patterns (`sk-[A-Za-z0-9_-]{16,}`, `AKIA[0-9A-Z]{16}`, `xox[baprs]-...`, JWT, PEM header line) and an unterminated-quote alternative, or amend the skill and the architecture to the narrower list. Add tests per pattern. Part of the same regex rewrite as CR-1 |
| CR-3 | Minor | src/docsync/redact.py:14-18 | False positives corrupt legitimate document content. End-to-end run (`docsync generate --offline` on a probe repo) produced `Description: Manage the API key: [REDACTED] it`, `Entry Point: keygen = [REDACTED]` (script named `keygen`) and `Dependency: keyring=[REDACTED]` (pin `keyring==23.0`); `keyboard: qwerty` and `hotkey: Ctrl` are also redacted because `key` matches anywhere inside the key name. The result is deterministic, so FR-17 holds, but the Dependencies and Entry Points sections lose real data | Require the sensitive word to be a whole token of the key name (`(?:^|[-_.])(token\|secret\|password\|passwd\|key\|credential)s?(?:$\|[-_.])`) and do not apply the `key=value` rule to `==`, `>=` or entry-point `name = module:attr` rows, or apply redaction by field rather than to the whole rendered text. Add false-positive tests |
| CR-4 | Minor | src/docsync/cli.py:60-65 | T13b rule: `--out` must end in `.md` and resolve inside `--repo`. This changes ADD-9: with a relative `--out` resolved against cwd, the default `docs/PROJECT_DOCS.md` is now rejected whenever cwd is outside `--repo` (test `test_default_out_is_rejected_when_cwd_is_outside_repo`), so `docsync generate --repo /some/repo` from elsewhere exits 2 although FR-1 and FR-18 promise that default. The restriction is a sound hardening choice but is not recorded in docs/01 or docs/02 | Needs a doc update: record the rule in docs/02-architecture.md (ADD-9) and docs/01-requirements.md (FR-18 or an assumption), or resolve a relative `--out` against `--repo` and drop the restriction on cwd. Human decision |
| CR-5 | Info | src/docsync/redact.py:6 | Placeholder is `[REDACTED]` (as in docs/02-architecture.md) whereas `.claude/skills/secret-safety/SKILL.md:27,48` says `***REDACTED***`. The architecture and all tests agree on `[REDACTED]` | Doc update to the skill (pipeline file, not product code); no code change |
| CR-6 | Info | src/docsync/cli.py:90 | Verbose diagnostic reads `DOCSYNC_GITHUB_TOKEN is set` instead of the skill's `token: set`, because `_KEY_VALUE` would redact `token: set`. Satisfies FR-8 and FR-20 (only set / not set is logged). This is a symptom of CR-3 | No change if CR-3 is fixed with whole-word matching; otherwise document the wording in docs/02 |
| CR-7 | Minor | src/docsync/collect.py:30,43 and src/docsync/github.py:50,54; src/docsync/cli.py:81,95,100,122 | Duplicated helpers: `_text` is identical in both modules, `_license` and the "sorted list of strings" helpers are near-duplicates; the `secrets=(token or "",)` expression and the env lookup are repeated in cli.py | Move `_text` (and a `_clean_strings`) into `docsync/model.py`; give cli.py one `_token()` helper and one `_redact(text, token)` helper |
| CR-8 | Minor | src/docsync/collect.py:129-130 | `UnicodeDecodeError` is a subclass of `ValueError`, so an undecodable test file is caught by the `(SyntaxError, ValueError)` branch and reported as "has a syntax error". Reproduced with a file containing `\xff\xfe\x00bad`: warning text was `tests/test_a.py has a syntax error; counted as a file with no tests`. The `OSError` branch at lines 131-132 is unreachable for decode errors and was not executed in the coverage run. `test_ec_8_undecodable_test_file_is_counted_with_one_warning` asserts only `len(warnings) == 1`, so it cannot catch this | Catch `UnicodeDecodeError` before `ValueError` with its own message; assert the message text in the test; add a test for the `OSError` branch (monkeypatch `Path.read_text`) |
| CR-9 | Info | src/docsync/collectors/__init__.py:1 | Empty stub package `collectors/` coexists with `collect.py` (PA-2, intentionally untouched per docs/04-impl-plan.md Section 8). Also `CollectError` and `GitHubError` (src/docsync/errors.py:12,16) are never raised in src/ (found only by `grep`: definitions only) | Human decision on removing the stub; either use the two errors or drop them. No unused imports found (`ruff check .` clean). No TODO, FIXME or stub markers in src/; `git grep -n NotImplementedError -- src` returns no matches |
| CR-10 | Minor | tests/test_github.py:120-141; tests/test_model.py:68-71; tests/test_cli.py:759-773, 977-987; tests/test_cli.py:424-449 | Weak tests. `test_fake_session_records_call_and_returns_response` and `test_fake_session_raises_configured_error` test the test double, not product code, and cannot fail on a product defect. `test_model_has_no_field_wrapper_class` asserts the absence of a name. The two source-grep tests (`test_no_bare_except_in_source`, `test_no_not_implemented_error_remains_in_source`) are static checks, not behaviour. `test_redaction_applied_to_file_and_console` asserts five behaviours (document, stdout, stderr, placeholder in file, placeholder in stderr), against the python-test-standards rule of one behaviour per test. `test_document_does_not_depend_on_file_creation_order` cannot fail on NTFS (EL-2). `__main__.py` shows 0% because the subprocess tests (`test_python_dash_m_docsync_*`) are not measured by coverage | Delete or fold the double-only tests into the tests that use the double; split the multi-assert test; optionally add `coverage` subprocess config or mark `__main__.py` with a justified `# pragma: no cover`; add a test for `collect.py:131-132` |
| CR-11 | Info | tests/test_collect.py:273-281 | EL-1: `test_scan_modules_symlinked_directory_is_not_followed` is skipped on this machine (Section 5, cmd 1: `1 skipped`; reason confirmed with `-rs`). EL-2 (NTFS ordering) and EL-3 (no live API test) also apply. All three must appear as Known Limitations in docs/06-verification.md and the PR description | Carry EL-1..EL-3 to step 7 and step 8; run the suite on Linux/CI if available (result otherwise `Not Found`) |
| CR-12 | Minor | src/docsync/cli.py:60-65 | `--out` validation residuals found by probing on Windows. Rejected correctly: `..` escape, absolute path outside repo, UNC `\\server\share\x.md`, drive-relative `C:x.md`, trailing dot or space, NTFS stream `x.md:evil`, sibling directory sharing a name prefix. Accepted: case-different path to the same repo (correct, resolves to the same directory), `CON.md`, `NUL.md` (Windows reserved device names), `.git/x.md`, and any existing in-repo `.md` such as `README.md`, which `generate` silently overwrites. Symlink escape is handled by `resolve()`; the check is time-of-check to time-of-use only, not an issue for a local CLI | Consider rejecting hidden directories (`.git`) and existing files that lack a docsync header, or documenting the overwrite behaviour. Not blocking |
| CR-13 | Info | src/docsync/cli.py:145; src/docsync/github.py:92 | The `except Exception` with `# noqa: BLE001` is acceptable: it is the last handler, narrower handlers precede it (`KeyboardInterrupt`, `BrokenPipeError`, `DocsyncError`, `OSError`), it is mandated by FR-19 (no traceback), it hides type and text unless `--verbose`, and a test proves both modes (`test_unexpected_exception_hides_type_and_text_without_verbose`, `..._shows_type_name_only_with_verbose`). No bare `except:` exists (AST test at `tests/test_cli.py:759`). Separately, `requests.Session()` is created and never closed, and `Session` honours `trust_env` (environment proxies and `~/.netrc`), which could replace the explicit `Authorization` header for api.github.com | Optionally use `with requests.Session() as s:` and `s.trust_env = False`. Not blocking |
| CR-14 | Info | docs/01-requirements.md:49-68 | Several "planned" acceptance-test names in docs/01 differ from the implemented names (e.g. `test_token_sent_as_bearer_and_never_logged` is implemented as `test_online_request_sends_bearer_authorization_header` plus `test_token_value_never_in_output_or_file`; `test_dotenv_never_opened` and others do match). Section 4 maps the real names | Update the Acceptance test column at step 7 or leave as planned names; no code change |
| CR-15 | Info | tests/test_cli.py:1-987 | One 987-line test file holds parsing, `--out` rules, generate, check, verbose and error-path tests, and the fake-token literal is repeated at lines 15, 429 and 456 | Split into `test_cli_args.py`, `test_cli_generate.py`, `test_cli_check.py` when next touched |
| CR-16 | Info | tests/test_cli.py:15,429,456; tests/test_redact.py:10,193,207 | Secret-scan matches are deliberate fake fixtures, see Section 5 classification. No match in product code is a credential | None |

### Secret-scan classification (command 5)

The grep returned matches in non-markdown files, so the "no matches" outcome did not occur. Every match was classified:

| Match | Classification |
|---|---|
| src/docsync/redact.py:8 `_TOKEN_PREFIXES = re.compile(r"(?:gh[pousr]_\|github_pat_)...")` | Product code, but it is the detection regex, not a credential. It is the only match under src/; no real credential is present in src/ |
| tests/test_cli.py:15, 429, 456 `ghp_A1b2C3d4E5f6G7h8I9j0K1` | Deliberate fake token-shaped test fixture proving redaction (EC-9) |
| tests/test_redact.py:10 `["ghp_", "gho_", ..., "github_pat_"]` | Test parameter list of prefixes, no value |
| tests/test_redact.py:193, 207 `ghp_{_BODY}` with `_BODY = "A1b2C3d4E5f6G7h8I9j0"` | Deliberate fake fixture |

No real credential was found. Matches for `sk-ant`, `AKIA` and `BEGIN .*PRIVATE KEY` in non-markdown files: none. The env-var fixtures `tok-SECRET-value-123` (tests/test_cli.py:207, tests/test_github.py:141) are also fake.

## 4. Requirement Verification Matrix

Status: Verified = implemented and a passing test exercises it; Verified (comment) = verified with a finding noted.

| FR/EC ID | Implemented in | Test | Status |
|---|---|---|---|
| FR-1 | src/docsync/cli.py:103-106 | tests/test_cli.py::test_generate_writes_default_output, test_generate_creates_missing_parent_directories | Verified |
| FR-2 | src/docsync/render.py:96-107 | tests/test_render.py::test_document_has_seven_sections_in_order | Verified |
| FR-3 | src/docsync/model.py:5; src/docsync/render.py:9-17 | tests/test_render.py::test_unresolved_fields_render_not_found, test_normalise_empty_values_become_not_found | Verified |
| FR-4 | src/docsync/github.py:9,65-74; src/docsync/render.py:45-57 | tests/test_github.py::test_only_stable_fields_rendered_extra_api_fields_never_appear, test_full_valid_payload_gives_the_six_fields | Verified |
| FR-5 | src/docsync/render.py:60-64; src/docsync/model.py:11-23 | tests/test_render.py::test_generation_info_has_no_volatile_values; tests/test_model.py::test_project_facts_has_no_timestamp_or_hash_field | Verified |
| FR-6 | src/docsync/redact.py:21-35; src/docsync/cli.py:79-81,95 | tests/test_cli.py::test_redaction_applied_to_file_and_console; tests/test_redact.py (33 tests) | Verified (comment: CR-1, CR-2, CR-3) |
| FR-7 | src/docsync/collect.py:59 (only `pyproject.toml` read), 88 (dot-names skipped) | tests/test_collect.py::test_dotenv_never_opened, test_collect_pyproject_opens_only_pyproject | Verified |
| FR-8 | src/docsync/github.py:33; src/docsync/cli.py:89-91,100 | tests/test_github.py::test_online_request_sends_bearer_authorization_header, test_ec_1_exception_text_and_token_are_never_echoed; tests/test_cli.py::test_token_value_never_in_output_or_file, test_verbose_reports_token_not_set | Verified |
| FR-9 | src/docsync/github.py:90 | tests/test_github.py::test_ec_5_token_unset_makes_no_session_calls | Verified |
| FR-10 | src/docsync/github.py:90 | tests/test_cli.py::test_offline_flag_makes_no_requests, test_check_offline_flag_makes_no_requests; tests/test_github.py::test_offline_flag_wins_even_if_token_is_set | Verified |
| FR-11 | src/docsync/github.py:30-47,94-95; src/docsync/cli.py:114-115 | tests/test_github.py::test_ec_1_request_exception_degrades_with_one_warning, test_non_2xx_status_other_than_404_403_degrades; tests/test_cli.py::test_generate_api_failure_warns_on_stderr_and_exits_0 | Verified |
| FR-12 | src/docsync/github.py:12,33 | tests/test_github.py::test_online_request_uses_timeout_of_5_seconds, test_online_failure_makes_no_retry | Verified |
| FR-13 | src/docsync/collect.py:140-157; src/docsync/render.py:96-107 | tests/test_integration.py::test_empty_repo_produces_full_document; tests/test_collect.py::test_ec_6_empty_repo_returns_complete_default_facts | Verified |
| FR-14 | src/docsync/collect.py:58-61,66-84 | tests/test_collect.py::test_ec_7_missing_pyproject_is_not_found_without_warning | Verified |
| FR-15 | src/docsync/cli.py:107-113 | tests/test_cli.py::test_check_in_sync_and_drift_exit_codes, test_check_detects_a_change_in_the_repository, test_check_crlf_copy_of_the_document_is_drift | Verified |
| FR-16 | src/docsync/cli.py:107-113 (read only, no write on the check branch) | tests/test_cli.py::test_check_does_not_write_when_file_is_missing, ..._when_file_has_drifted, ..._when_in_sync | Verified |
| FR-17 | src/docsync/collect.py:36,82,103; src/docsync/render.py:107; src/docsync/cli.py:102,105 | tests/test_integration.py::test_generate_twice_is_byte_identical, test_generate_twice_via_python_dash_m_is_byte_identical (EL-2 applies to the creation-order test) | Verified |
| FR-18 | src/docsync/cli.py:39-51,68-76 | tests/test_cli.py::test_flags_and_defaults, test_all_flags_are_parsed_for_generate, test_check_subcommand_accepts_the_same_flags | Verified (comment: CR-4) |
| FR-19 | src/docsync/cli.py:120-147 | tests/test_cli.py::test_invalid_input_exit_2_no_traceback, test_keyboard_interrupt_exits_2_without_traceback, test_unexpected_exception_hides_type_and_text_without_verbose | Verified |
| FR-20 | src/docsync/cli.py:88-91 | tests/test_cli.py::test_verbose_output_is_redacted, test_without_verbose_no_diagnostics_are_printed | Verified |
| EC-1 | src/docsync/github.py:34-37 | tests/test_github.py::test_ec_1_request_exception_degrades_with_one_warning, test_ec_1_timeout_warning_says_timed_out, test_ec_1_mocked_timeout_returns_without_waiting | Verified |
| EC-2 | src/docsync/github.py:13-16,39-40 | tests/test_github.py::test_ec_2_api_404_degrades | Verified |
| EC-3 | src/docsync/github.py:13-16,39-40 | tests/test_github.py::test_ec_3_api_403_rate_limit_degrades | Verified |
| EC-4 | src/docsync/github.py:41-47,65-74 | tests/test_github.py::test_ec_4_invalid_json_degrades, test_ec_4_non_object_json_payload_degrades, test_ec_4_single_missing_key_gives_only_that_field_not_found | Verified |
| EC-5 | src/docsync/github.py:90 | tests/test_github.py::test_ec_5_token_unset_makes_no_session_calls, test_ec_5_blank_token_is_treated_as_unset; tests/test_cli.py::test_ec_5_generate_without_token_makes_no_requests | Verified |
| EC-6 | src/docsync/collect.py:140-157 | tests/test_collect.py::test_ec_6_empty_repo_returns_complete_default_facts, test_ec_6_scan_modules_empty_repo_gives_empty_tuple; tests/test_render.py::test_ec_6_default_facts_render_a_full_seven_section_document | Verified |
| EC-7 | src/docsync/collect.py:60-61 | tests/test_collect.py::test_ec_7_missing_pyproject_is_not_found_without_warning | Verified |
| EC-8 | src/docsync/collect.py:62-65,127-132 | tests/test_collect.py::test_ec_8_unreadable_pyproject_gives_one_warning, test_ec_8_undecodable_pyproject_gives_one_warning, test_ec_8_syntax_error_test_file_is_counted_with_one_warning, test_ec_8_undecodable_test_file_is_counted_with_one_warning | Verified (comment: CR-8; `collect.py:131-132` not executed) |
| EC-9 | src/docsync/redact.py:21-35 | tests/test_redact.py::test_ec_9_redact_token_prefix_is_replaced, test_ec_9_redact_literal_secret_is_replaced | Verified (comment: CR-1, CR-2) |
| EC-10 | src/docsync/cli.py:71-72 | tests/test_cli.py::test_ec_10_nonexistent_repo_exits_2_with_one_line, test_ec_10_file_as_repo_exits_2_with_one_line | Verified |
| EC-11 | src/docsync/cli.py:19,54-57,74-75 | tests/test_cli.py::test_ec_11_invalid_github_repo_is_rejected, test_ec_11_valid_github_repo_is_accepted, test_ec_11_invalid_github_repo_exits_2_with_one_line | Verified |
| EC-12 | src/docsync/cli.py:108-111 | tests/test_cli.py::test_ec_12_check_missing_file_is_drift, test_check_missing_parent_directory_is_drift | Verified |
| EC-13 | src/docsync/collect.py:62-63 | tests/test_collect.py::test_ec_13_malformed_toml_gives_not_found_and_one_warning | Verified |
| EC-14 | src/docsync/github.py:90 | tests/test_github.py::test_ec_14_github_repo_omitted_makes_no_session_calls, test_ec_14_blank_github_repo_is_treated_as_omitted; tests/test_cli.py::test_ec_14_generate_without_github_repo_makes_no_requests | Verified |
| NFR-1 | src/docsync/cli.py:84-117 (offline path) | tests/test_perf.py::test_offline_under_1s (best of 3 = 0.0110 s, Section 5; budget 1.0 s target, 2.0 s hard) | Verified |
| NFR-2 | src/docsync/github.py:12,33 | tests/test_github.py::test_ec_1_mocked_timeout_returns_without_waiting; live online timing: Not Found (EL-3) | Partially verified |
| NFR-3 | whole package | `--cov` total 97% (Section 5, cmd 2); requirement is 85%. Note the `--cov-fail-under=85` flag was not passed in the mandated command | Verified |
| NFR-4 | tests/ | Test names `test_ec_1_*` to `test_ec_14_*` exist for all 14 ECs (EC-9 added in commit 18aa32b) | Verified |
| NFR-5 | pyproject.toml (`requests>=2.32.0` only; `requires-python = ">=3.11"`); imports in src/ are standard library plus `requests` | `pyproject.toml` inspection | Verified |
| NFR-6 | whole repository | `ruff check .` : `All checks passed!` | Verified |
| NFR-7 | tests/conftest.py:8-14 (autouse fixture blocks `requests.Session.request`) | tests/test_model.py::test_autouse_fixture_blocks_real_requests | Verified (EL-3: no live test by design) |
| NFR-8 | src/docsync/render.py:107; src/docsync/collect.py:103 | tests/test_integration.py::test_generate_twice_is_byte_identical | Verified (EL-2 caveat) |
| NFR-9 | src/docsync/cli.py:127-147 (exit codes 0, 1, 2; no prompts) | tests/test_cli.py exit-code tests | Verified |
| NFR-10 | src/docsync/redact.py:21-35 | tests/test_redact.py, tests/test_cli.py::test_redaction_applied_to_file_and_console | Not fully verified: AKIA, sk-ant, PEM and unterminated-quote values pass through (CR-2) |

## 5. Command Output

### Command 1: `python -m pytest -q`

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\parag_bansal\PycharmProjects\GitHub\agentic-sdlc-docsync
configfile: pyproject.toml
testpaths: tests
plugins: platformdirs-4.12.3, cov-7.1.0
collected 298 items

tests\test_cli.py ...................................................... [ 18%]
..........................................                               [ 32%]
tests\test_collect.py .............................s...............      [ 47%]
tests\test_github.py ................................................... [ 64%]
............                                                             [ 68%]
tests\test_integration.py ............                                   [ 72%]
tests\test_model.py ..........                                           [ 75%]
tests\test_perf.py .
[perf] offline generate best of 3: 0.0110 s (all: 0.0131, 0.0113, 0.0110); target < 1.0 s: target met; hard limit < 2.0 s
.                                                    [ 76%]
tests\test_redact.py .................................                   [ 87%]
tests\test_render.py .....................................               [100%]

======================= 297 passed, 1 skipped in 3.67s ========================
```

### Command 2: `python -m pytest --cov=src/docsync --cov-report=term-missing -q`

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\parag_bansal\PycharmProjects\GitHub\agentic-sdlc-docsync
configfile: pyproject.toml
testpaths: tests
plugins: platformdirs-4.12.3, cov-7.1.0
collected 298 items

tests\test_cli.py ...................................................... [ 18%]
..........................................                               [ 32%]
tests\test_collect.py .............................s...............      [ 47%]
tests\test_github.py ................................................... [ 64%]
............                                                             [ 68%]
tests\test_integration.py ............                                   [ 72%]
tests\test_model.py ..........                                           [ 75%]
tests\test_perf.py .
[perf] offline generate best of 3: 0.0111 s (all: 0.0116, 0.0120, 0.0111); target < 1.0 s: target met; hard limit < 2.0 s
.                                                    [ 76%]
tests\test_redact.py .................................                   [ 87%]
tests\test_render.py .....................................               [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.14.2-final-0 _______________

Name                                 Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------------------------
src\docsync\__init__.py                  1      0      0      0   100%
src\docsync\__main__.py                  4      4      2      0     0%   3-8
src\docsync\cli.py                      99      0     16      0   100%
src\docsync\collect.py                  79      2     14      1    97%   111->108, 131-132
src\docsync\collectors\__init__.py       0      0      0      0   100%
src\docsync\errors.py                    4      0      0      0   100%
src\docsync\github.py                   47      0      8      0   100%
src\docsync\model.py                     6      0      0      0   100%
src\docsync\redact.py                   17      0      2      0   100%
src\docsync\render.py                   42      0      4      0   100%
--------------------------------------------------------------------------------
TOTAL                                  299      6     46      1    97%
======================= 297 passed, 1 skipped in 3.87s ========================
```

### Command 3: `ruff check .`

```text
All checks passed!
```

### Command 4: `python -m pip_audit`

```text
No known vulnerabilities found
Name    Skip Reason
------- ----------------------------------------------------------------------
docsync Dependency not found on PyPI and could not be audited: docsync (0.1.0)
exit=0
```

### Command 5: `git grep -nE "(sk-ant|ghp_|github_pat|BEGIN .*PRIVATE KEY|AKIA)" -- . ":!*.md"`

```text
src/docsync/redact.py:8:_TOKEN_PREFIXES = re.compile(r"(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]+")
tests/test_cli.py:15:_TOKEN_SHAPED = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
tests/test_cli.py:429:    shaped = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
tests/test_cli.py:456:    shaped = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
tests/test_redact.py:10:@pytest.mark.parametrize("prefix", ["ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"])
tests/test_redact.py:193:        f"Authorization: Bearer abc ghp_{_BODY} https://u:p@h.io "
tests/test_redact.py:207:    text = f"password=x ghp_{_BODY}"
exit=0
```

(`exit=0` is grep's exit status: matches were found. Classification is in Section 3.)

### Command 6: `git grep -n NotImplementedError -- src`

```text
exit=1
```

(Exit 1 from `git grep` means no match: no `NotImplementedError` remains in src/.)

### Command 7: `python -m pip list` filtered for requests and its dependencies

```text
certifi                 2026.7.22
charset-normalizer      3.5.2
idna                    3.20
requests                2.34.2
urllib3                 2.8.0
```

### Command 8: skipped-test reason, `python -m pytest -q -rs` filtered with `grep -i skip`

```text
SKIPPED [1] tests\test_collect.py:273: EL-1: directory symlink creation is not permitted in this environment (Windows needs elevated privileges or Developer Mode); see docs/04-impl-plan.md section 10 Environment Limitations
======================= 297 passed, 1 skipped in 3.90s ========================
```

### Probe results (scratch scripts outside the repository)

Selected `redact()` outputs:

```text
'keyboard: qwerty' -> 'keyboard: [REDACTED]'
'hotkey: Ctrl' -> 'hotkey: [REDACTED]'
'AKIAIOSFODNN7EXAMPLE' -> 'AKIAIOSFODNN7EXAMPLE'
'sk-ant-api03-abcdef' -> 'sk-ant-api03-abcdef'
'-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----' -> '-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----'
'git+https://tok@github.com/o/r.git' -> 'git+https://tok@github.com/o/r.git'
'key = "unterminated' -> 'key = "unterminated'
'https://user:pw@host/x' -> 'https://[REDACTED]@host/x'
'Authorization: token ghp_xyz' -> 'Authorization: [REDACTED]'
```

ReDoS timings (seconds, one `.sub` call on the pattern named):

```text
URL pattern, input "key"+"a"*200000 : 387.15 s (full redact() call, first probe)
URL pattern, input "a"*n            n=5000: 0.361   n=10000: 1.269   n=20000: 5.393
URL pattern, input "key"+"a"*n      n=5003: 0.336   n=10003: 1.382   n=20003: 5.246
KV pattern,  input "a-"*n + "="     len=5001: 1.242 len=10001: 5.051 len=20001: 26.507
TOK, AUTH, BEARER patterns          all 0.000 to 0.002 at 20,000 chars
```

End-to-end false positives (`docsync generate --offline` on a probe `pyproject.toml`):

```text
| Description | Manage the API key: [REDACTED] it |
| Entry Point | keygen = [REDACTED] |
| Dependency | keyring=[REDACTED] |
| Dependency | requests>=2.32 |
```

`--out` and `--github-repo` probes (repo = temp directory):

```text
ACCEPT  <repo>\x.md                      ACCEPT  <REPO upper-case>\x.md (same directory)
reject  x.md.   x.md<space>   x.md:evil   ..\r2\x.md   \\server\share\x.md   C:x.md
ACCEPT  CON.md  NUL.md  .git\x.md  pyproject.md
github-repo True : a/b  -/-      False : a/b\n  a/b<space>  ../b  a/..  a/.  a/b/c  a\b  a/b%
```

## 6. Verdict

**Changes requested.**

Row counts are in the table below. One row (Security) is `Fail`, which makes the overall verdict `Changes requested` under the review rules.

| Verdict | Count | Areas |
|---|---|---|
| Pass | 2 | Code Clarity, Dependency Safety |
| Pass with comment | 4 | Correctness, Error Handling, Test Coverage, DRY Principle |
| Fail | 1 | Security |

Blocking findings: **CR-1** (ReDoS in `redact.py`, Major) and **CR-2** (redaction pattern gaps against the skill and NFR-10, Major; needs a human decision between adding the patterns or narrowing the skill and architecture). CR-3 shares the same regex rewrite and should be fixed together with them. CR-4 needs a human decision and a doc update but does not block. All other findings (CR-5..CR-16) are Minor or Info and do not block.

Secret scan: the grep returned matches in non-markdown files (so it did not return "no matches"); all seven lines were classified as the detection regex (`src/docsync/redact.py:8`) or deliberate fake test fixtures. No real credential is present and no match in `src/` is a credential.

## 7. Re-review after remediation

Targeted re-review. Sections 1 to 6 above are the original record and are retained unchanged; nothing in them was edited, renumbered or reformatted. IDs CR-1 to CR-16 keep their meaning; new findings start at CR-17.

### 7.1 Review metadata

| Field | Value |
|---|---|
| Reviewed commit | `9e52a1d` (`git rev-parse --short HEAD`, confirmed at the start and the end of this re-review) |
| Date | 2026-10-08 |
| Reviewer | code-reviewer |
| Original review | Reviewed commit 18aa32b (section 1); the review document was committed as 03a965c (verdict `Changes requested`) |
| Remediation commits | 546f4b1 (CR-4 code), 675750f (CR-4 docs), 2cfa41a (secret-safety skill aligned), 0446e96 (T20 added to the plan, RO-2 and RO-3), 9e52a1d (T20 redactor rewrite) |
| Product files changed since 03a965c | `src/docsync/cli.py`, `src/docsync/redact.py`, `tests/test_cli.py`, `tests/test_integration.py`, `tests/test_redact.py` (from `git diff 03a965c HEAD --stat`); `collect.py`, `github.py`, `model.py`, `render.py`, `errors.py` and `pyproject.toml` are unchanged |
| Documents changed since 03a965c | `docs/01-requirements.md`, `docs/02-architecture.md`, `docs/04-impl-plan.md`, `README.md`, `.claude/skills/secret-safety/SKILL.md` |
| Not reviewed | Pre-existing uncommitted pipeline files (`.claude/*`, `CLAUDE.md`, `.env.example`, `evidence/*`) are not product code and were not reviewed. The skill file `.claude/skills/secret-safety/SKILL.md` was read only to compare its pattern list with the implementation |
| Tests | 381 collected, 380 passed, 1 skipped (EL-1), up from 297 passed and 1 skipped (Section 5, command 1) |
| Method | Probe scripts were kept outside the repository (`C:\Users\parag_bansal\AppData\Local\Temp\rr\`); the old redactor was extracted with `git show 03a965c:src/docsync/redact.py` to `C:\Users\parag_bansal\AppData\Local\Temp\old_redact.py` and loaded with `importlib`. No repository file other than this document was modified |

### 7.2 Re-assessed review areas

Every one of the seven areas was re-assessed; none was carried forward without a fresh look. Rows that were not driven by the remediation (Code Clarity, Dependency Safety) were still re-checked because `redact.py` was rewritten and `pip_audit` was re-run.

| Area | Original verdict (section 2) | Re-review verdict | Evidence | Action |
|---|---|---|---|---|
| Correctness | Pass with comment | Pass with comment | FR-1 and FR-18 now match the code: the default is `repo / _DEFAULT_OUT` (`src/docsync/cli.py:20,77`), an explicit `--out` is validated by `_check_out` (`cli.py:63-68`); docs/01-requirements.md:49 (FR-1) and :66 (FR-18), docs/02-architecture.md:182 and :226, README.md:39 agree. Real run in 7.3 (CR-4): default landed in `<repo>/docs/PROJECT_DOCS.md` from a cwd outside the repo, `check` returned `in sync`. CR-3 false positives are gone (7.3). Open: CR-8 (undecodable test file reported as a syntax error, `collect.py` unchanged since 03a965c). Residual redaction false positives are Minor (CR-18, CR-19) | Fix CR-8; consider CR-18 and CR-19 |
| Security | Fail | Pass with comment | CR-1 fixed: 20,000-character inputs now take 0.0002 to 0.0068 s versus 2.1 to 13.9 s before; all 13 compiled patterns have only bounded quantifiers (7.3, structural check; `tests/test_redact.py:582`). CR-2 fixed for sk-, AKIA, xox, JWT, PEM and userinfo (7.3; tests `test_redact.py:253,273,288,299`). CR-3 fixed (tests `test_redact.py:381,389,410,424`). The redactor is imported only by `cli.py:16` (grep) and `tests/test_redact.py:616` enforces it. Secret scan: no match is real credential material (7.5). Residual: partial or missed redaction in unusual shapes (CR-17, CR-20, CR-21), none a Blocker or Major | Track CR-17, CR-20, CR-21 as Minor hardening |
| Error Handling | Pass with comment | Pass with comment | `--out` validation still raises one-line `UsageError` (`cli.py:63-68`): real run printed `docsync: error: --out must end in .md, got 'x.txt'` (exit 2) and `docsync: error: --out must be inside --repo, got 'docs\\X.md'` (exit 2) (7.3). Tests: `tests/test_cli.py:484,491,497,517,600,648,660`. `collect.py:131-132` (OSError on a test file) is still never executed (7.5 coverage: `collect.py 97%  111->108, 131-132`) and CR-8 is still open | Address CR-8 and the `collect.py:131-132` test (CR-10) |
| Test Coverage | Pass with comment | Pass with comment | 380 passed, 1 skipped; total 97%; `cli.py`, `redact.py`, `github.py`, `render.py`, `model.py`, `errors.py` 100% (7.5). New tests cover ReDoS (`tests/test_redact.py:528`), bounded quantifiers (`:569,577,582`), each provider pattern (`:253`), PEM (`:273`), blob heuristic and its false-positive guards (`:299,310,321,344,381`), CR-3 cases (`:389,410,424`), choke point end to end (`tests/test_integration.py:285`), and the CR-4 default-out cases (`tests/test_cli.py:531,553,581,600,615`). Gaps: CR-10 weak tests unchanged; `test_redact_is_idempotent` (`tests/test_redact.py:198`) checks one sample and a 20,000-case fuzz found 11 counterexamples (CR-22); no test for quoted-key or plural-key forms (CR-17) | Add tests with CR-17, CR-22; keep CR-10 open |
| Code Clarity | Pass | Pass with comment | `redact.py` is 85 lines with a module docstring that states the invariants (`redact.py:1-6`), a named helper per concern (`_rule`, `_redact_mixed_case_blob`, shared `_KEEP_PREFIX`, `_SCHEME`, `_STRONG_KEYS`, `redact.py:15,26,32-34`) and an ordering comment (`redact.py:36-37`). Comment: the 13 rules in `_RULES` (`redact.py:38-70`) are dense regexes with no per-rule label, so the reader must decode each one (CR-27) | None blocking; see CR-27 |
| DRY Principle | Pass with comment | Pass with comment | Within `redact.py` duplication is avoided: one `_rule` factory, one `_KEEP_PREFIX`, one `_SCHEME` (`redact.py:26,32,33`). The original DRY findings are untouched (CR-7): `secrets=(token or "",)` is still written twice (`cli.py:86,100`), `DOCSYNC_GITHUB_TOKEN` is still read twice (`cli.py:105,127`), `_text` is still duplicated in `collect.py` and `github.py` (both files unchanged since 03a965c) | CR-7 stays open (non-blocking) |
| Dependency Safety | Pass | Pass | `python -m pip_audit` re-run: `No known vulnerabilities found` (7.5). `pyproject.toml` is unchanged since 03a965c (`git diff 03a965c HEAD --stat -- pyproject.toml` is empty). Not Found: advisories for the declared floor `requests>=2.32.0` (only installed versions are audited), as in section 2 | None |

Row count in 7.2: Pass 1, Pass with comment 6, Fail 0, Carried forward 0.

### 7.3 Finding status

| CR id | Original severity | Status | Evidence | Notes |
|---|---|---|---|---|
| CR-1 | Major | Resolved | `src/docsync/redact.py:39-69` (every quantifier bounded, patterns compiled once into `_RULES`); tests `tests/test_redact.py::test_redos_regression_pathological_input_completes_under_1_second` (`:528`, 18 pathological inputs), `test_every_quantifier_in_every_redaction_pattern_is_bounded` (`:582`), `test_patterns_are_compiled_once_into_a_module_level_tuple` (`:594`). Measurements below | Old redactor (`git show 03a965c:src/docsync/redact.py`) versus the new one, same machine, same run |
| CR-2 | Major | Resolved | `redact.py:39-48,56-57` and `:69`; tests `tests/test_redact.py:253` (each provider class), `:273` (PEM headers), `:288` (token-only userinfo of 20 or more characters), `:299` (mixed-case blob), `:432` (unterminated quote for strong keys), `tests/test_integration.py:285` (end to end) | The decision was to add the skill's patterns (not to narrow the skill). Demonstration and the honest list of what is still not covered are below |
| CR-3 | Minor | Resolved | `redact.py:34,58-68`; tests `tests/test_redact.py:381` (benign lines), `:389`, `:410`, `:424` | Strong keys (token, secret, password, passwd, credential) redact any value; bare `key` redacts only token-shaped values of 20 or more characters. Demonstration below |
| CR-4 | Minor | Resolved | `src/docsync/cli.py:20,63-68,77`; tests `tests/test_cli.py:531` (default with cwd outside the repo), `:553` (cwd inside the repo), `:581` (explicit relative `--out` from another cwd), `:600` (explicit relative `--out` escaping the repo rejected), `:615` (`check` from outside the repo); docs: docs/01-requirements.md:49 and :66, docs/02-architecture.md:182 and :226, README.md:39, docs/04-impl-plan.md:174 and :198 (RO-3) | Resolved by changing the behaviour (human decision RO-3). Real run below |
| CR-5 | Info | Resolved | `.claude/skills/secret-safety/SKILL.md:27` now reads "replaced with `[REDACTED]` (the canonical placeholder, as in docs/02-architecture.md and the tests)"; `src/docsync/redact.py:11` `PLACEHOLDER = "[REDACTED]"` is unchanged | CR-5 was resolved by aligning the secret-safety skill to the implemented and architecturally documented placeholder. This was a specification change, not a code change, and it is recorded here so the finding is not silently dropped. Commit 2cfa41a |
| CR-6 | Info | Accepted | `src/docsync/cli.py:95` still prints `DOCSYNC_GITHUB_TOKEN is {state}` | The strong-key rule would still turn `token: set` into `token: [REDACTED]` (CR-3 demonstration below), so the wording is kept deliberately; it satisfies FR-8 and FR-20 |
| CR-7 | Minor | Open | `src/docsync/cli.py:86,100,105,127`; `collect.py` and `github.py` unchanged | Duplicated helpers remain; non-blocking |
| CR-8 | Minor | Open | `collect.py` unchanged since 03a965c; coverage still misses `collect.py:131-132` (7.5) | Undecodable test file still reported as a syntax error; non-blocking |
| CR-9 | Info | Open | `src/docsync/collectors/__init__.py` still present; `git grep -n NotImplementedError -- src` returns no matches (7.5) | Human decision on the stub unchanged |
| CR-10 | Minor | Open | test double and static-check tests unchanged; `tests/test_cli.py` is now 1075 lines | The "no ReDoS or AKIA or sk-ant or PEM test" part of the original Test Coverage evidence is now closed; the weak tests are not |
| CR-11 | Info | Open | 1 skipped test in 7.5 (EL-1) | Carry EL-1 to EL-3 to steps 7 and 8 |
| CR-12 | Minor | Open | `cli.py:63-68` unchanged in substance | `.git/x.md`, `CON.md` and overwrite of existing `.md` files still accepted; non-blocking |
| CR-13 | Info | Accepted | `cli.py` and `github.py` `except Exception` handlers unchanged | Acceptable as stated in section 3 |
| CR-14 | Info | Open | docs/01-requirements.md acceptance-test names (planned) unchanged | Update at step 7 or leave |
| CR-15 | Info | Open | `tests/test_cli.py` grew from 987 to 1075 lines | Split when next touched |
| CR-16 | Info | Accepted | 7.5 re-classification of every secret-scan match | All matches are deliberate fake fixtures or the detection regex; no real credential |

#### CR-1 proof: old versus new redactor on 20,000-character inputs

Command: `python -I C:\Users\parag_bansal\AppData\Local\Temp\rr\p1.py` (old module loaded from `C:\Users\parag_bansal\AppData\Local\Temp\old_redact.py` with `importlib`, new module imported from `src/`).

```text
case | len | old s | new s
"a"*20000 | 20000 | 3.023 | 0.0054
"a-"*10000+"=" | 20001 | 13.915 | 0.0049
"sk-"*6600 | 19800 | 10.333 | 0.0002
"eyJ"*6600 | 19800 | 2.940 | 0.0068
"aA1"*6700 | 20100 | 2.099 | 0.0054
"a"*20000+"://" | 20003 | 2.900 | 0.0033
```

Structural check (walks `re._parser.parse` of every compiled pattern in `docsync.redact._RULES` and reports any `MAX_REPEAT`, `MIN_REPEAT` or possessive repeat whose upper bound is `MAXREPEAT`; the checker was first sanity-checked on `a+b{2,5}` and correctly flagged the `+` and not the `{2,5}`):

```text
sanity unbounded detector: [(1, True), (2, False)]
0 unbounded: []
1 unbounded: []
2 unbounded: []
3 unbounded: []
4 unbounded: []
5 unbounded: []
6 unbounded: []
7 unbounded: []
8 unbounded: []
9 unbounded: []
10 unbounded: []
11 unbounded: []
12 unbounded: []
rules: 13
```

All 13 patterns have only bounded quantifiers. The repository's own test (`tests/test_redact.py:582`) performs the same check.

#### CR-2 proof: what is now replaced, and what is not

Command: `python -I C:\Users\parag_bansal\AppData\Local\Temp\rr\p2.py` (excerpt, input then output).

```text
'AKIAIOSFODNN7EXAMPLE'  ->  '[REDACTED]'
'key sk-ant-api03-abcdefghijklmnop1234 x'  ->  'key [REDACTED] x'
'-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAabc+/def==\n-----END RSA PRIVATE KEY-----'  ->  '[REDACTED]-----END RSA PRIVATE KEY-----'
'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U'  ->  '[REDACTED]'
'https://user:pass@example.com/x'  ->  'https://[REDACTED]@example.com/x'
'git+https://abcdefghijklmnopqrstuvwxyz0123@github.com/o/r.git'  ->  'git+https://[REDACTED]@github.com/o/r.git'
'xoxb-1234567890-abcdefghij'  ->  '[REDACTED]'
'git+https://tok@github.com/o/r.git'  ->  'git+https://tok@github.com/o/r.git'
'key = "unterminated'  ->  'key = "unterminated'
'API key is abc123def'  ->  'API key is abc123def'
```

Still deliberately NOT covered (reported honestly, not hidden): a token-only userinfo shorter than 20 characters such as `git+https://tok@github.com/o/r.git`; a bare `key` assignment with a value under 20 characters such as `key = "unterminated`; and free prose such as `API key is abc123def`. The PEM footer line `-----END ... PRIVATE KEY-----` is left in place (only the header and body are replaced). These are design choices recorded in RO-2 and RO-3 and in the redaction tests (`tests/test_redact.py:424`), traded against false positives; further residuals are in 7.4.

#### CR-3 proof: false positives gone, real secrets still replaced

```text
'keygen = 1'  ->  'keygen = 1'
'keyring=abc'  ->  'keyring=abc'
'API key: rotate it'  ->  'API key: rotate it'
'key = value'  ->  'key = value'
'keyboard: qwerty'  ->  'keyboard: qwerty'
'hotkey: Ctrl'  ->  'hotkey: Ctrl'
'keyring==23.0'  ->  'keyring==23.0'
'api_key=ghp_A1b2C3d4E5f6G7h8I9j0K1'  ->  'api_key=[REDACTED]'
'key=abcdefghijklmnopqrstuvwxyz'  ->  'key=[REDACTED]'
'token: set'  ->  'token: [REDACTED]'
```

End to end: a real `docsync generate` on a probe repo whose `description` is `Manage the API key: rotate it` produced `| Description | Manage the API key: rotate it |` in `docs/PROJECT_DOCS.md` (in the original review the same description came out as `Manage the API key: [REDACTED] it`).

#### CR-4 proof: real run from a cwd outside the repo

Setup: probe repo `C:\Users\parag_bansal\AppData\Local\Temp\rr\target_repo` (a `pyproject.toml` only), cwd `C:\Users\parag_bansal\AppData\Local\Temp\rr\elsewhere` (outside the repo), `PYTHONPATH` set to this repository's `src`, real `python -m docsync`.

```text
cwd=/c/Users/parag_bansal/AppData/Local/Temp/rr/elsewhere
--- default out
wrote C:/Users/parag_bansal/AppData/Local/Temp/rr/target_repo/docs/PROJECT_DOCS.md
exit=0
/c/Users/parag_bansal/AppData/Local/Temp/rr/elsewhere:
total 4
drwxr-xr-x 1 AzureAD+ParagBansal 4096 0 Oct  8 18:47 .
drwxr-xr-x 1 AzureAD+ParagBansal 4096 0 Oct  8 18:47 ..

/c/Users/parag_bansal/AppData/Local/Temp/rr/target_repo/docs:
total 4
drwxr-xr-x 1 AzureAD+ParagBansal 4096   0 Oct  8 18:47 .
drwxr-xr-x 1 AzureAD+ParagBansal 4096   0 Oct  8 18:47 ..
-rw-r--r-- 1 AzureAD+ParagBansal 4096 906 Oct  8 18:47 PROJECT_DOCS.md
--- check default
in sync
exit=0
--- explicit relative out from cwd (outside repo) -> expect rejected
docsync: error: --out must be inside --repo, got 'docs\\X.md'
exit=2
--- explicit relative out that resolves inside repo from cwd
wrote out.md
exit=0
out.md
--- explicit relative out ../x.md from cwd resolving in repo
wrote ../target_repo/rel.md
exit=0
docs
pyproject.toml
rel.md
sub
--- bad ext
docsync: error: --out must end in .md, got 'x.txt'
exit=2
```

Result: the default lands in `<repo>/docs/PROJECT_DOCS.md` and nothing is written in the cwd; `check` compares the same file; an explicit relative `--out` is still resolved against the cwd (`out.md` written in the cwd `.../target_repo/sub`, `../target_repo/rel.md` written inside the repo) and is still validated (`.md` suffix and inside `--repo`). The documents named in the decision were updated: docs/01-requirements.md:49 (FR-1) and :66 (FR-18); docs/02-architecture.md:182 (section 9) and :226 (revision row 1.2); README.md:39 (Usage); plus docs/04-impl-plan.md:174 and :198 (RO-3).

### 7.4 New findings

Probed adversarially with `C:\Users\parag_bansal\AppData\Local\Temp\rr\p2.py` and `p3.py`. Confirmed good: only `cli.py` imports the redactor (`src/docsync/cli.py:16` is the sole `from docsync.redact import` in `src/`; `tests/test_redact.py:616` enforces it); a secret inside one table cell such as `\| password: hunter2 \| next \|` is redacted (the cell delimiter is excluded from values); uppercase and mixed-case keys (`PASSWORD=`, `PassWord:\t`, `Password : x`) are redacted; a `[REDACTED]` already in the input passes through unchanged. No Blocker and no Major finding was found.

| CR id | Severity | File:line | Issue | Recommendation |
|---|---|---|---|---|
| CR-17 | Minor | src/docsync/redact.py:58-68 | The key/value rules miss common shapes (probe, input then output). JSON or YAML quoted keys: `{"password": "hunter2"}` and `"token": "abc123"` are unchanged (a closing quote sits between the key and the colon). Plural or suffixed keys: `passwords=hunter2`, `secrets: hunter2`, `SECRET_KEY=abc123`, `private_key=short` are unchanged (the strong word must be immediately followed by the separator; bare `key` needs 20 or more characters). Key and value in separate table cells: the row `\| password \| hunter2 \|` is unchanged. Multi-word values: `password=a b c` becomes `password=[REDACTED] b c`. Arrow form: `password => hunter2` becomes `password =[REDACTED] hunter2` | Allow an optional closing quote and an optional `s` or `_key` suffix before the separator in the strong-key rule and add the cases to `tests/test_redact.py`; or document these as known limits in docs/02 section 7 |
| CR-18 | Minor | src/docsync/redact.py:58-63 | The strong-key rule redacts ordinary prose in a generated document (probe): `the password: required for login` becomes `the password: [REDACTED] for login`; `Set the secret: see docs` becomes `Set the secret: [REDACTED] docs`; `This tool reads a token: from the env` becomes `... token: [REDACTED] the env`. Deterministic, so FR-17 holds, but project descriptions lose words. This is the documented trade-off (a missed secret in a committed file is permanent) | Accept as a design trade-off and record it in docs/02 section 7, or require the value to contain a digit or symbol; human decision |
| CR-19 | Minor | src/docsync/redact.py:40,69 | Over-redaction by generic rules. Blob heuristic: `getUserAccountSettingsFromRemoteServerHandler2024Version` becomes `[REDACTED]`; `https://github.com/SomeOrganisationName/VeryLongRepositoryName1234567890` becomes `https://github.[REDACTED]`; `src/docsync/SomeVeryLongPackageNameWithMixedCase123/AnotherLongDirectoryName456/file.py` becomes `[REDACTED].py`; `pkg:SomeOrganisation/VeryLongRepositoryNameWithCaps1234567` becomes `pkg:[REDACTED]`. The `sk-` rule redacts the library name in `sk-learn-compatible-estimators` (16 or more name characters after `sk-`). The blob cases need a mixed-case run of 40 or more characters, so they are uncommon | Accept and document, or drop `/` from the blob class and require a digit and a symbol; add a false-positive test for a long GitHub URL |
| CR-20 | Minor | src/docsync/redact.py:48,69 | The documented chunking leaves residues. A mixed-case run of 4,135 characters is redacted in one chunk of 4,096 and the final 39 characters stay visible (probe); a run of 4,106 leaves 10. base64url secrets (`-` and `_`) are split by the blob class `[A-Za-z0-9+/]`, so a 44-character base64url string (`Ab1_` repeated 11 times) is unchanged. A PEM body longer than 8,192 characters would leave its tail, and the `-----END ... PRIVATE KEY-----` footer line is always left | Loop until no run of 40 or more remains (still linear) or raise the bound; add `-_` to a second blob rule; document the residuals. Low practical risk: the tail is a fragment and real PEM keys are under 8,192 characters |
| CR-21 | Minor | src/docsync/redact.py:56-57 | URL userinfo residuals (probe): `postgres://user:p@ss@host/db` becomes `postgres://[REDACTED]@ss@host/db` (the part of the password after the first `@` stays); `https://user:pa/ss@host` is unchanged (a `/` in the password); token-only userinfo under 20 characters is unchanged (deliberate, see CR-2 notes) | Redact up to the last `@` before the first `/` after the scheme; document the 20-character rule in docs/02 |
| CR-22 | Minor | src/docsync/redact.py:77-78; tests/test_redact.py:198; docs/02-architecture.md:154 | The idempotency claim `redact(redact(x)) == redact(x)` is not true for adversarial input. Probe: `password="abc"def` becomes `password=[REDACTED]def` on the first pass and `password=[REDACTED]` on the second. A seeded fuzz of 20,000 random strings built from a secret-related alphabet found 11 non-idempotent cases. Impact is low because `cli.py` applies redaction exactly once per output, so `generate` and `check` stay deterministic (FR-17); the test `test_redact_is_idempotent` uses one benign sample | Either remove the idempotency claim from the docstring and docs/02, or fix the quoted-value alternative so a closing quote must be followed by a delimiter; add a small property-style test |
| CR-23 | Minor | docs/02-architecture.md:154 | Section 7 (Security Design) is stale relative to `src/docsync/redact.py`. It lists only the `gh*_` and `github_pat_` prefixes, `Authorization` and `Bearer`, `scheme://user:pass@host` and "key=value pairs whose key contains token/secret/password/passwd/key/credential". The code also redacts sk-, AKIA, Slack `xox`, JWT, PEM private-key header and body, token-only userinfo of 20 or more characters and mixed-case base64 blobs; bare `key` is now limited to token-shaped values of 20 or more characters; the order differs (code order is provider tokens, header, URL, key=value, blob); every quantifier is bounded; the revision table (docs/02-architecture.md:226) records only CR-4, not T20 | Update section 7 and add a revision row for T20, RO-2 and RO-3 at step 7 (design document, no code change) |
| CR-24 | Info | .claude/skills/secret-safety/SKILL.md:29-39,47 | The skill's pattern list disagrees with the implementation. It shows unbounded forms (`sk-[A-Za-z0-9_-]{16,}`, `ghp_[A-Za-z0-9]{20,}`, `[A-Za-z0-9+/]{40,}`) whereas the code bounds every quantifier (`redact.py:39-69`); `gh[pousr][A-Za-z0-9]{20,}` has no underscore, so it would also match ordinary words starting `gho`, `ghp` and so on followed by 20 alphanumerics, while the code requires `gh[pousr]_`; `eyJ[A-Za-z0-9-]{10,}.` has an unescaped dot and no underscore or second segment, while the code requires `eyJ` + 8 to 2048 characters + `.` + a second segment (`redact.py:44-46`). Line 47 says the verification grep returns "no matches", but it matches the detection regex and the fake fixtures (7.5) | Mark the skill list as illustrative and state that `src/docsync/redact.py` is authoritative, or paste the real bounded patterns; reword line 47 to "no match outside `redact.py` and `tests/`" (pipeline file, not product code) |
| CR-25 | Info | docs/01-requirements.md:113; docs/04-impl-plan.md:60 | Two residual statements still describe the pre-CR-4 default. Q6 in docs/01 says `--out PATH (default docs/PROJECT_DOCS.md)`; the T13b row in docs/04 says a relative `--out` and the default resolve against the cwd (ADD-9). Both are superseded by FR-1, FR-18, docs/02 section 9 and docs/04:174 and :198 (RO-3), which are correct | Add "(resolved against `--repo`; CR-4)" to Q6, or leave as the historical decision record |
| CR-26 | Info | src/docsync/redact.py:80-82 | Literal-secret replacement is a plain substring replace, so a very short literal corrupts other text (probe: `redact("hello", secrets=["l"])` gives `he[REDACTED][REDACTED]o`; literals `a` and `b` turn `password=x` into `p[REDACTED]ssword=x`). In the product the only literal is the `DOCSYNC_GITHUB_TOKEN` value, so this needs a one-character token, which is not realistic. The placeholder text `[REDACTED]` already present in input is left as is and cannot be told apart from a real redaction (acceptable) | None required; optionally ignore literals shorter than 8 characters, with a test |
| CR-27 | Info | src/docsync/redact.py:38-70 | The 13 rules in `_RULES` are anonymous dense regexes; a reader or a test failure refers to a tuple index rather than a name, and the only explanation is the one ordering comment at lines 36-37 | Give each rule a short name (a `NamedTuple` or a dict) so tests and error output can say which rule fired |

### 7.5 Command output (fresh, run from the repo root at 9e52a1d)

Command: `python -m pytest -q`

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\parag_bansal\PycharmProjects\GitHub\agentic-sdlc-docsync
configfile: pyproject.toml
testpaths: tests
plugins: platformdirs-4.12.3, cov-7.1.0
collected 381 items

tests\test_cli.py ...................................................... [ 14%]
...............................................                          [ 26%]
tests\test_collect.py .............................s...............      [ 38%]
tests\test_github.py ................................................... [ 51%]
............                                                             [ 54%]
tests\test_integration.py .............                                  [ 58%]
tests\test_model.py ..........                                           [ 60%]
tests\test_perf.py .
[perf] offline generate best of 3: 0.0097 s (all: 0.0133, 0.0114, 0.0097); target < 1.0 s: target met; hard limit < 2.0 s
.                                                    [ 61%]
tests\test_redact.py ................................................... [ 74%]
...........................................................              [ 90%]
tests\test_render.py .....................................               [100%]

======================= 380 passed, 1 skipped in 4.49s ========================
```

Command: `python -m pytest --cov=src/docsync --cov-report=term-missing -q`

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\parag_bansal\PycharmProjects\GitHub\agentic-sdlc-docsync
configfile: pyproject.toml
testpaths: tests
plugins: platformdirs-4.12.3, cov-7.1.0
collected 381 items

tests\test_cli.py ...................................................... [ 14%]
...............................................                          [ 26%]
tests\test_collect.py .............................s...............      [ 38%]
tests\test_github.py ................................................... [ 51%]
............                                                             [ 54%]
tests\test_integration.py .............                                  [ 58%]
tests\test_model.py ..........                                           [ 60%]
tests\test_perf.py .
[perf] offline generate best of 3: 0.0151 s (all: 0.0153, 0.0152, 0.0151); target < 1.0 s: target met; hard limit < 2.0 s
.                                                    [ 61%]
tests\test_redact.py ................................................... [ 74%]
...........................................................              [ 90%]
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
src\docsync\redact.py                   21      0      4      0   100%
src\docsync\render.py                   42      0      4      0   100%
--------------------------------------------------------------------------------
TOTAL                                  306      6     48      1    97%
======================= 380 passed, 1 skipped in 4.42s ========================
```

Command: `ruff check .`

```text
All checks passed!
```

Command: `python -m pip_audit`

```text
No known vulnerabilities found
Name    Skip Reason
------- ----------------------------------------------------------------------
docsync Dependency not found on PyPI and could not be audited: docsync (0.1.0)
```

Result: `No known vulnerabilities found`; the project itself is skipped because it is not on PyPI (expected).

Command: `git grep -nE "(sk-ant|ghp_|github_pat|BEGIN .*PRIVATE KEY|AKIA)" -- . ":!*.md"`

```text
src/docsync/redact.py:39:    _rule(r"(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,255}", PLACEHOLDER),
src/docsync/redact.py:41:    _rule(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])", PLACEHOLDER),
src/docsync/redact.py:48:    _rule(r"-----BEGIN [A-Z ]{0,40}PRIVATE KEY-----[A-Za-z0-9+/=\r\n]{0,8192}", PLACEHOLDER),
tests/test_cli.py:15:_TOKEN_SHAPED = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
tests/test_cli.py:429:    shaped = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
tests/test_cli.py:456:    shaped = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
tests/test_integration.py:290:    github = "ghp_A1b2C3d4E5f6G7h8I9j0K1L2M3N4O5P6Q7R8"
tests/test_integration.py:291:    aws = "AKIAIOSFODNN7EXAMPLE"
tests/test_integration.py:292:    anthropic = "sk-ant-api03-abcdefghijklmnop1234"
tests/test_redact.py:18:@pytest.mark.parametrize("prefix", ["ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"])
tests/test_redact.py:201:        f"Authorization: Bearer abc ghp_{_BODY} https://u:p@h.io "
tests/test_redact.py:215:    text = f"password=x ghp_{_BODY}"
tests/test_redact.py:223:_GH_TOKEN = "ghp_A1b2C3d4E5f6G7h8I9j0K1L2M3N4O5P6Q7R8"
tests/test_redact.py:241:        "sk-ant-api03-abcdefghijklmnop1234",
tests/test_redact.py:244:        "github_pat_11ABCDEFG0abcdefghijkl_mnopqrstuvwxyz0123456789",
tests/test_redact.py:246:        "AKIAIOSFODNN7EXAMPLE",
tests/test_redact.py:267:        "-----BEGIN RSA PRIVATE KEY-----",
tests/test_redact.py:268:        "-----BEGIN PRIVATE KEY-----",
tests/test_redact.py:269:        "-----BEGIN OPENSSH PRIVATE KEY-----",
tests/test_redact.py:270:        "-----BEGIN EC PRIVATE KEY-----",
tests/test_redact.py:462:        "sk-ant-api03-abcdefghijklmnop1234",
tests/test_redact.py:463:        "AKIAIOSFODNN7EXAMPLE",
tests/test_redact.py:497:        "ghp_", "sk-ant", "AKIA", "xoxb-", "eyJ", "MIIEow", "abc123def456", "s3cr3t",
tests/test_redact.py:513:    "repeated github prefix": "ghp_" * 5000,
tests/test_redact.py:515:    "repeated pem header": "-----BEGIN PRIVATE KEY-----" * 740,
```

Command: `git grep -n NotImplementedError -- src`

```text
(no output; exit code 1, meaning no matches)
```

Secret-scan classification. The grep returned matches in non-markdown files, as expected (so it did not return "no matches"); 25 lines, all classified:

| Match | Classification |
|---|---|
| `src/docsync/redact.py:39,41,48` | The detection regexes (`gh[pousr]_` and `github_pat_`, `AKIA[0-9A-Z]{16}`, `-----BEGIN ... PRIVATE KEY-----`); they are patterns, not credential material. These are the only matches in product code |
| `tests/test_cli.py:15,429,456` | Deliberate fake token-shaped fixture `ghp_A1b2C3d4E5f6G7h8I9j0K1` |
| `tests/test_integration.py:290-292` | Deliberate fake fixtures: a made-up `ghp_` string, AWS's documented example key id `AKIAIOSFODNN7EXAMPLE`, and a made-up `sk-ant-api03-abcdefghijklmnop1234` |
| `tests/test_redact.py:18,201,215,223,241,244,246,462,463` | Deliberate fake fixtures (same family; `github_pat_11ABCDEFG0abcdefghijkl_...` is a made-up body) |
| `tests/test_redact.py:267-270` | PEM header lines only, with no key material, used as inputs |
| `tests/test_redact.py:497` | A list of prefixes asserted to be absent from the redacted output |
| `tests/test_redact.py:513,515` | Repeated prefixes used as pathological ReDoS inputs |

No match is real credential material, and no match sits in product code other than the detection patterns in `src/docsync/redact.py`. No secret-shaped string is hard-coded outside `redact.py` and `tests/`.

### 7.6 Updated overall verdict

**Approved.**

No row is `Fail` (7.2: Pass 1, Pass with comment 6), and there is no Blocker or Major finding that is open: CR-1 and CR-2 (Major) are Resolved, CR-3 to CR-6 are Resolved or Accepted, and the new findings CR-17 to CR-27 are Minor or Info. Blocking CR ids: none. Open non-blocking items: CR-7, CR-8, CR-9, CR-10, CR-11, CR-12, CR-14, CR-15 (original) and CR-17 to CR-27 (new); CR-22 and CR-23 should be handled at step 7 (docs/02 section 7 refresh and the idempotency claim).

This verdict supersedes section 6; section 6 is retained unchanged as the original record.

### 7.7 Final remediation round (T21), remediation freeze and deferred findings

Appended after the re-review verdict (7.6); sections 1 to 7.6 are unchanged. This subsection records the author's evidence for T21 (commits `167d039` plan, `4bd4fb8` CLAUDE.md rule 9, `f837f74` T21a, and the commit that carries this subsection for T21b and T21c). It is **not** a new independent review: the verdict in 7.6 was issued at `9e52a1d`, and `src/docsync/redact.py` changed afterwards in `f837f74`.

**Remediation freeze (decision RO-4).** T21 is the final remediation round for step 6. After T21 is approved, no further code or documentation remediation happens in step 6. Every remaining finding is disclosed as a Known Limitation in step 7 and step 8 and must reappear verbatim in the Known Limitations sections of docs/06-verification.md and docs/07-pr-description.md. Only a High severity security or correctness defect may reopen the freeze, and only after the human is asked explicitly.

#### 7.7.1 Findings fixed in T21

| CR id | Status | Evidence | Notes |
|---|---|---|---|
| CR-17 | Resolved | `redact.py:62` (`_STRONG_KEY`: plural, separated suffix, optional quote), `redact.py:63` (`_VALUE`), `redact.py:91`, table rule at `redact.py:97`; tests `test_redact.py:658` (quoted keys), `:677` (plural and suffixed), `:694` (separate table cells), `:713` (quoted bare `key`) | Every new pattern is bounded and compiled at module level; `test_redact.py:591` fails on any unbounded quantifier |
| CR-19 | Resolved for URLs, repository names, topics, licence identifiers, paths and `sk-` package names | `redact.py:16` (`_redact_sk_key`: digit required), `redact.py:22` and `:29` (path-like runs), `redact.py:37`; tests `test_redact.py:766` (14 strings that must survive byte-identical, including the six named in T21) and `:782` | A regression was caught before commit: the first path heuristic skipped the AWS example secret `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`; it was tightened and has its own test. Residual: long camel-case identifiers, see CR-29 |
| CR-22 | Resolved by a wording change plus a partial fix (the chosen option) | docstring `redact.py:107`; tests `test_redact.py:804` (`password="abc"def` is replaced in one pass), `:828` (20,000 seeded delimited strings, 0 failures), `:844` (the glued-secrets limitation is stated, not hidden); docs/02-architecture.md:154 | Chosen because exact idempotency cannot be proven for arbitrary input. Measured with a grammar fuzz of 150,000 strings per seed (seeds 99, 7, 2026): T20 code 0.38%, 0.41%, 0.38% non-idempotent; T21a code 0.11%, 0.14%, 0.13%; 0 of 150,000 when the pieces are space-delimited. The remaining cases are secrets pasted together with no delimiter (CR-31) |
| CR-23 | Resolved | docs/02-architecture.md:154 rewritten; revision row 1.3 added | Document stated: docs/02-architecture.md section 7. False claims: only `gh*_` prefixes, Authorization, Bearer, `user:pass@` and "key contains token/secret/password/passwd/key/credential"; "output is idempotent". Correction: the real pattern set, order, bounds, strong and weak key rules, blob heuristic, and the qualified idempotency statement |
| CR-24 | Resolved | `.claude/skills/secret-safety/SKILL.md:32` (`gh[pousr]_` with the underscore), `:35` (JWT form), `:42` (the list is illustrative; `redact.py` is authoritative and bounded), `:50` (verification line) | Document stated: the secret-safety skill. False claims: `gh[pousr]` without the underscore, the JWT pattern with an unescaped dot and one segment, and "no matches" for the verification grep. The unbounded `{n,}` forms are kept as illustration and declared non-authoritative |
| CR-25 | Resolved | docs/01-requirements.md:113 (Q6 annotated), docs/04-impl-plan.md:60 (T13b row marked superseded for the default) | Document stated: Q6 and the T13b row. False claim: the default `--out` resolves against the cwd. Correction: annotations that point to CR-4 and RO-3; the historical record is kept, not rewritten |
| CR-28 | Resolved (T21c) | CLAUDE.md golden rule 9, commit `4bd4fb8`; section 8 below corrected | New finding, severity Minor, process defect: artifact dates were assumed or taken from the human's instructions instead of git. The initial review's `Date` was recorded as 2026-10-07 but `git log -1 --format=%cs 03a965c` gives 2026-10-08. Section 8 row 1.0 is corrected. **Section 1 of this document still shows 2026-10-07**: it is the frozen original record and is deliberately not rewritten; this entry is the correction by appending. Dates in docs/01 to docs/04 were checked against their first git commits and match |

Not fixed in T21b, and why. T21b fixes only statements where a document contradicts the implemented code. Left unchanged: the planned acceptance-test names in docs/01 that differ from the implemented names (CR-14: naming, traceability by id is intact); the historical task descriptions of T3 and T4 in docs/04 (a record of what each task did at the time); the README Quick start, whose code fence is never closed and swallows a pasted PR template (a formatting defect, not a contradiction with the code); and any wording that is merely incomplete or stylistic.

#### 7.7.2 Deferred findings: disclosed as Known Limitations

Status for every row: **Deferred, disclosed as Known Limitation.** Severity is as recorded in section 3 or 7.4 (or here for the new ids). These rows must reappear verbatim in the Known Limitations sections of docs/06-verification.md and docs/07-pr-description.md.

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
| CR-27 | Info | The 13 rules in `_RULES` are unnamed | Readability only (freeze rule) |
| CR-29 | Info | New: a long camel-case identifier of 40 or more characters containing a digit is redacted by the blob heuristic | Cannot be separated from random base64 by entropy (measured: identifiers 4.2 to 4.4 bits, random base64 4.3 and above); excluding it would miss real secrets |
| CR-30 | Minor | New: the widened key rules redact configuration names and table headers: `max_tokens = 4096` becomes `max_tokens = [REDACTED]`, and a header cell pair `| Secret | Description |` becomes `| Secret | [REDACTED] |` | Cosmetic and reversible; plural and suffixed key names are exactly what CR-17 asked to catch |
| CR-31 | Info | New: secrets pasted together with no delimiter are not idempotent (`AKIA...EXAMPLEsk-ant-...`), because replacing the first changes the character the second one is anchored to | Measured at 0.11% to 0.14% of structured fuzz strings and 0 of 150,000 when delimited; the first pass already hides both |
| CR-32 | Info | New: the path-like heuristic can skip a random base64 secret that has several long mostly lower-case segments | Measured: 3 of 159,922 random mixed-case base64 secrets (0.002%) were skipped |
| CR-33 | Info | New: an `sk-` key whose body contains no digit is not redacted | Needed to spare names such as `sk-learn-extension`; about 0.3% of random 32-character alphanumeric bodies have no digit |
| CR-34 | Info | New: an unquoted secret value that contains `}` is redacted only up to the brace | The brace stop keeps JSON structure intact and the output idempotent |

#### 7.7.3 Corrections to the deferred record after T22 (appended; 7.7.1 and 7.7.2 above are not edited)

Added after the human granted the single freeze exception (T22, commit `3487008`, git date 2026-10-09) and after the delta re-review (7.8). Where this subsection disagrees with 7.7.1 or 7.7.2, this subsection is correct.

| Item | What 7.7.1 or 7.7.2 said | Correct statement |
|---|---|---|
| CR-33 | Listed in 7.7.2 as a deferred Info finding: "an `sk-` key whose body contains no digit is not redacted" | **Resolved by T22** (`3487008`, severity High). It is removed from the deferred list, and the 7.7.2 row for CR-33 must **not** be copied into the Known Limitations of docs/06-verification.md or docs/07-pr-description.md. Its consequence is recorded as CR-35 (7.8.6) |
| CR-27 | "The 13 rules in `_RULES` are unnamed" | The real count is **14**: 13 explicit rules (`_EXPLICIT_RULES`, `redact.py:67`) plus 1 heuristic rule (`_HEURISTIC_RULES`, `redact.py:103`). The finding itself (rules are unnamed) is unchanged and still deferred |
| CR-19 | 7.7.1 says `sk-` package names are spared because the `sk-` rule requires a digit | That condition was removed by T22 (the human ruled that a prefix match is sufficient for explicit patterns). `sk-learn-extension-package-name` is redacted again; this is CR-35. The URL, repository-name, topic, licence-identifier and path parts of CR-19 remain resolved |
| Line numbers in 7.7.1 | `redact.py` lines cited as of `f837f74` | At `3487008`: `_is_word_like` `:16`, `_is_path_like` `:23`, `_redact_mixed_case_blob` `:31`, `_STRONG_KEY` `:56`, `_VALUE` `:57`, strong-key rule `:87`, table rule `:93`, `sk-` rule `:69`, `redact` `:110`. `_redact_sk_key` no longer exists |

**Final deferred list as of the T22 gate** (each to be disclosed as a Known Limitation with severity and justification, and reproduced verbatim in docs/06-verification.md and docs/07-pr-description.md): CR-7 to CR-16, CR-18, CR-20, CR-21, CR-26, CR-27, CR-29, CR-30, CR-31, CR-32 and CR-34, with severities and justifications exactly as in 7.7.2. For CR-31 step 7 must also include the AC7 reasoning recorded as RO-6 in docs/04-impl-plan.md.

**Raised by the delta re-review (7.8), not on the human's list because they did not yet exist:** CR-35 (Minor) and CR-38 (Info) are disclosed limitations of the redactor; CR-37 (Minor) is corrected by this subsection; **CR-36 (Minor) is open and needs a human decision**: docs/02-architecture.md section 7 still says `sk-` keys are redacted "only if they contain a digit", which the code no longer does. Under the remediation freeze it was not edited; it is either a one-clause documentation correction approved by the human, or a disclosed Known Limitation.

## 7.8 Delta re-review at 3487008

Appended after 7.7; sections 1 to 7.7 are unchanged. Carried forward from 7.6 without re-review (one line): every mandatory area other than Security, Test Coverage and DRY Principle, every file other than `src/docsync/redact.py` and `tests/test_redact.py`, and the status of every finding not named below. The uncommitted pipeline files in the working tree (`.claude/*`, `evidence/*`, `.env.example`) are not product code and were neither reviewed nor touched.

### 7.8.1 Metadata

| Item | Value |
|---|---|
| Reviewed commit | `3487008` (`git rev-parse --short HEAD` returned `3487008`) |
| Commit date (git-derived, `git log -1 --format=%cs 3487008`) | 2026-10-09 |
| Diff range reviewed | `9e52a1d..3487008`, restricted to `src/docsync/redact.py` and `tests/test_redact.py` |
| Files at that commit | `src/docsync/redact.py` (123 lines), `tests/test_redact.py` (990 lines) |
| Reviewer | code-reviewer subagent (independent delta re-review; scratch probes in a directory outside the repository) |
| Purpose | Closes the integrity gap recorded in 7.7: T21a (`f837f74`) and T22 (`3487008`) changed the redactor after the approved re-review (7.6, `9e52a1d`) and were not independently reviewed |

```text
 src/docsync/redact.py |  68 +++++++---
 tests/test_redact.py  | 357 ++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 410 insertions(+), 15 deletions(-)
```

### 7.8.2 Delta assessment of the three in-scope areas

| Area | Verdict | Evidence | Action |
|---|---|---|---|
| Security | Pass with comment | Every explicit pattern redacts a no-digit, no-uppercase variant (7.8.3 probe output; tests `tests/test_redact.py:859`, `:887`, `:899`, `:923`). `redact.py:63-99` `_EXPLICIT_RULES` holds 13 plain-string rules, no callback (independent check: `callable explicit: []`). The only mixed-case plus digit condition is `redact.py:31-42` (`_redact_mixed_case_blob`), bound to the single unprefixed blob rule at `redact.py:103-105`. No unbounded quantifier (7.8.4b). Worst pathological input 6.4 ms (7.8.5). Secret scan: no real credential material (7.8.7). Comment: anchoring and case residuals that let some prefixed tokens through, see CR-38 | None blocking. Record CR-35 to CR-38 |
| Test Coverage | Pass with comment | `redact.py` 33 statements, 0 missed, 6 branches, 0 partial, 100% (7.8.7). T22 tests: `test_redact.py:859` (the CR-33 case), `:887` (11 parametrised no-digit prefixed secrets), `:899` (PEM), `:923` (6 key shapes), `:932` (sk package name redacted, documented), `:951` (words ending in `sk`), `:959`-`:973` (group structure), `:981` (blob heuristic keeps its condition). Comment: no test pins the boundary behaviour recorded in CR-38 (`abcsk-...`, `SK-...`, 15-character `sk-` body, JWT after `-`), so a later change could alter it silently; `test_cr_33_explicit_rules_use_plain_replacements_with_no_heuristic_callback` (`:965`) proves the explicit group has no callbacks but not that no explicit regex embeds a lookahead that mimics a mixed-case condition (none does today) | Add boundary tests when the file is next touched |
| DRY Principle | Pass with comment | One redaction function, `redact.py:110` (7.8.4a). `_STRONG` (`redact.py:53`) is reused by `_STRONG_KEY` (`:56`) and the table rule (`:95`); `_SCHEME` (`:52`) is reused by both URL rules (`:85`, `:86`); `_KEEP_PREFIX` (`:51`) by five rules; `_rule` (`:45`) is the single compile helper. Comment: the fragment `[\"']?[ \t]{0,8}[:=][ \t]{0,8}` is written out twice (`:56` and `:89`) and the Authorization rule repeats `[ \t]{0,8}:[ \t]{0,8}` (`:79`) | Info only; consolidate when next touched |

### 7.8.3 CR-33 (High, found after 7.6 and fixed in T22): status Resolved

Evidence: scratch script `probe.py` outside the repository imported the committed module and called `redact()` on a no-digit variant of every explicit pattern. Every line below is the verbatim probe output (full output in 7.8.8).

```text
sk                           REDACTED   '[REDACTED]'        <- sk-abcdefghijklmnopqrstuvwxyz (no digit, no uppercase)
ghp                          REDACTED   '[REDACTED]'
github_pat                   REDACTED   '[REDACTED]'
gho                          REDACTED   '[REDACTED]'
ghu                          REDACTED   '[REDACTED]'
ghs                          REDACTED   '[REDACTED]'
ghr                          REDACTED   '[REDACTED]'
AKIA                         REDACTED   '[REDACTED]'
xoxb                         REDACTED   '[REDACTED]'
xoxp                         REDACTED   '[REDACTED]'
jwt                          REDACTED   '[REDACTED]'
pem                          REDACTED   '[REDACTED]-----END PRIVATE KEY-----'
json                         REDACTED   '{"password": [REDACTED]}'
suffixed                     REDACTED   'SECRET_KEY=[REDACTED]'
plural                       REDACTED   'passwords: [REDACTED]'
table                        REDACTED   '| password | [REDACTED] |'
weakkey                      REDACTED   'key=[REDACTED]'
weakkey_json                 REDACTED   '{"key": [REDACTED]}'
```

Hidden-condition hunt: all 13 explicit regexes were read at `redact.py:68-98`. None embeds a digit or case requirement; the only digit or case test in the module is in `_redact_mixed_case_blob` (`redact.py:39-40`), attached only to the blob rule. The `AKIA` rule requires 16 upper-case-or-digit characters (a character class, not a mix condition), so `AKIAABCDEFGHIJKLMNOP` matches. Conclusion: CR-33 is Resolved for the case the human ruled on (prefix or key-name match is sufficient).

What is still not caught (honest list, from the boundary probes; all by design of the anchors or length bounds, none a mixed-case or digit condition):

```text
letters+sk                   UNCHANGED  'abcsk-abcdefghijklmnopqrstuvwxyz'
SK upper                     UNCHANGED  'SK-abcdefghijklmnopqrstuvwxyz'
Sk                           UNCHANGED  'Sk-abcdefghijklmnopqrstuvwxyz'
sk short15                   UNCHANGED  'sk-abcdefghijklmno'
sk newline split             UNCHANGED  'sk-abcdefgh\nijklmnopqrstuv'
sk prefixed by digit         UNCHANGED  '1sk-abcdefghijklmnopqrstuvwxyz'
GHP upper                    UNCHANGED  'GHP_abcdefghijklmnopqrstuvwxyz'
ghp short                    UNCHANGED  'ghp_abcdefghijklmnopqrs'
AKIA 17 tail                 UNCHANGED  'AKIAABCDEFGHIJKLMNOPQ'
AKIA prefixed                UNCHANGED  'XAKIAABCDEFGHIJKLMNOP'
xoxe                         UNCHANGED  'xoxe-abcdefghijklmnop'
jwt short seg                UNCHANGED  'eyJabcdefg.abcdefgh.sig'
jwt prefixed hyphen          UNCHANGED  'x-eyJabcdefgh.abcdefgh.sig'
```

Caught as required: `sk-` after a hyphen, underscore or colon (`my-[REDACTED]`), a hyphen-split body (`sk-abcdefgh-ijklmnop-qrstuv`), two `sk-` tokens directly adjacent, `ghp_` after letters, 16-character `sk-` body, `Bearer` with 8 characters. Short tokens and `PRIVATE KEY` footers are discussed in CR-38. Real GitHub, Anthropic and AWS tokens are lower-case prefixed, exact length and normally delimited, so these residuals are low likelihood; they are recorded, not blocking.

### 7.8.4 The four invariants

| Invariant | Holds | Evidence |
|---|---|---|
| (a) Exactly one redaction function | Yes | `grep -rn "def redact\|def _redact" src/docsync` returned `redact.py:31: def _redact_mixed_case_blob` and `redact.py:110: def redact`. Reviewer agrees the former is a rule callback (a `re.sub` replacement helper for the blob rule, `redact.py:104`), not a second entry point: nothing else calls it and `cli.py` imports only `redact` |
| (b) No unbounded quantifier | Yes | Independent structural walk of `re._parser.parse` over every pattern in `_RULES`: `rules 14 13 1`, `unbounded: []` (scratch `probe.py`, not the repo test). Enforcing repo test: `tests/test_redact.py:591` `test_every_quantifier_in_every_redaction_pattern_is_bounded` (with `:578` and `:586` proving the checker itself detects `a+`, `a*`, `a{2,}`) |
| (c) All patterns compiled at module level | Yes | `redact.py:45-48` (`_rule` compiles), used only inside the tuple literals at `redact.py:67` and `:103`; `redact()` at `:110-123` calls only `.sub` and `str.replace`. Repo tests `test_redact.py:603` (tuple of `re.Pattern`) and `:609` (`re.compile` monkeypatched to raise during `redact()`) |
| (d) `render.py` does not use the redactor; `cli.py` is the only importer | Yes | `grep -rn "redact" src/docsync --include=*.py \| grep import` returned only `src/docsync/cli.py:16: from docsync.redact import redact`; `render.py` imports (`re`, `__version__`, `model`) contain no redactor and `grep -n redact src/docsync/render.py` returned nothing. Repo test `test_redact.py:625` `test_only_the_cli_module_imports_the_redactor` |

### 7.8.5 Performance

Independent timings (scratch `probe.py`, one call per input, `time.perf_counter`; full list in 7.8.8). The nine required inputs, plus ten extra repeated-prefix inputs:

```text
a*20000                            len= 20000      3.2 ms
a-*10000=                          len= 20001      3.0 ms
sk-*6600                           len= 19800      0.2 ms
eyJ*6600                           len= 19800      3.1 ms
aA1*6700                           len= 20100      3.4 ms
password_*2200                     len= 19800      6.4 ms
| secret |*2000                    len= 20000      3.7 ms
password="+a*20000                 len= 20010      3.2 ms
Ab1/*5000                          len= 20000      5.6 ms
ghp_*5000                          len= 20000      0.2 ms
AKIA*5000                          len= 20000      3.1 ms
key=*4000                          len= 16000      2.7 ms
-----BEGIN PRIVATE KEY-----*1000   len= 27000      2.8 ms
eyJ..*                             len= 19200      1.4 ms
https://*2000                      len= 25000      4.3 ms
bearer *                           len= 21000      3.4 ms
authorization:*                    len= 22400      1.1 ms
xoxb-*                             len= 20000      0.7 ms
a/*10000                           len= 20000      5.3 ms
```

Worst measured: 6.4 ms for about 20,000 characters (limit in the repo test: 1 second). `python -m pytest -q -m perf tests/test_redact.py` result is in 7.8.8 (26 passed). No super-linear behaviour was observed.

### 7.8.6 New findings

CR-28 to CR-34 already exist in 7.7; ids below start at CR-35 and are never reused.

| CR id | Severity | File:line | Issue | Recommendation | Blocking |
|---|---|---|---|---|---|
| CR-35 | Minor | `src/docsync/redact.py:69`; `tests/test_redact.py:932` | Consequence of the CR-33 ruling: any `sk-` token of 16 or more `[A-Za-z0-9_-]` characters that is not preceded by an alphanumeric is redacted, so a package or repository name such as `sk-learn-extension-package-name` becomes `[REDACTED]` (confirmed: result equals `[REDACTED]`). The test at `:932` documents this as intended. Words ending in `sk` (`risk-assessment-...`, `task-scheduler-...`) are not affected (test `:951`). Cosmetic and reversible, consistent with RO-2 | Disclose as a Known Limitation in step 7 and step 8 alongside CR-18 and CR-30 | No |
| CR-36 | Minor | `docs/02-architecture.md:154` | Stale after T22: the row still says "`sk-` keys (only if they contain a digit)". The code at `redact.py:69` has no such condition. The row also names only `_RULES` and does not mention the `_EXPLICIT_RULES` and `_HEURISTIC_RULES` groups | Correct the sentence at step 7 (the freeze forbids a step 6 remediation) or disclose; the human decides | No |
| CR-37 | Minor | `docs/05-code-review.md` 7.7.1, 7.7.2 (frozen, not edited) | Stale facts in 7.7, corrected here by appending. (1) Line numbers cited in 7.7.1 no longer point at the cited code: `redact.py:16` was `_redact_sk_key`, now `_is_word_like` (the function is gone); `:62` `_STRONG_KEY` is now `:56`; `:63` `_VALUE` now `:57-61`; `:91` now `:89`; table rule `:97` now `:94-98`; docstring `:107` now `:110-117`; `:22` and `:29` path-like helpers are now `:23` and `:16`; `:37` is now `:31-42`. Test line numbers cited in 7.7.1 (`:591`, `:658`, `:677`, `:694`, `:713`, `:766`, `:782`, `:804`, `:828`, `:844`) were re-checked and still point at the cited tests. (2) The CR-19 row says `_redact_sk_key` requires a digit: superseded by T22. (3) The CR-33 deferred row in 7.7.2 (Info, "an `sk-` key without a digit is not redacted", justified by sparing `sk-learn-extension`) is superseded: CR-33 was High and is Resolved (7.8.3). It must NOT be copied as a Known Limitation into docs/06 and docs/07; CR-35 replaces it. (4) CR-27 says 13 rules; the real count is 14 (13 explicit plus 1 heuristic, `rules 14 13 1`) | Treat 7.8 as the authoritative correction; carry CR-35 instead of the old CR-33 row into Known Limitations | No |
| CR-38 | Info | `src/docsync/redact.py:68-77` | Anchor, case and length residuals for prefixed tokens (probe list in 7.8.3): `sk-` directly after a letter or digit, upper-case `SK-`/`GHP_`/`XOXB-`, a 15-character `sk-` body, an `AKIA` id with extra trailing alphanumerics or an alphanumeric before it, `xoxe-` tokens, a JWT whose first two segments are under 8 characters or that follows `-` or `_`, `ghp_` bodies under 20 characters, a `sk-` token split by a newline. The PEM rule redacts the header and body but leaves the `-----END ... PRIVATE KEY-----` footer (not secret). The anchors exist to avoid redacting words that end in `sk` and similar; all missed shapes are non-standard for real tokens | Disclose as a Known Limitation; add boundary tests when next touched | No |

Also checked and unchanged (no new id): the key-shape false positives from T21a (`max_tokens = 4096` becomes `max_tokens = [REDACTED]`, reproduced in the probe) are CR-30; the path-like exemption residual is CR-32; runs over 4,096 characters are CR-20 (the blob bound `{40,4096}` at `redact.py:104` is unchanged by T22); an unquoted secret containing `}` is CR-34. Prose such as `password hunter` and `the password is hunter` is not redacted (no `:` or `=`), which is outside FR-6 key=value scope and is recorded here as an observation.

### 7.8.7 Fresh command output (run from the repo root at 3487008)

Command: `python -m pytest -q`

```text
$ python -m pytest -q
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
[perf] offline generate best of 3: 0.0229 s (all: 0.0311, 0.0380, 0.0229); target < 1.0 s: target met; hard limit < 2.0 s
.                                                    [ 51%]
tests\test_redact.py ................................................... [ 62%]
........................................................................ [ 78%]
..............................................................           [ 91%]
tests\test_render.py .....................................               [100%]

======================= 455 passed, 1 skipped in 11.78s =======================
```

Command: `python -m pytest -q -m perf tests/test_redact.py`

```text
$ python -m pytest -q -m perf tests/test_redact.py
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\parag_bansal\PycharmProjects\GitHub\agentic-sdlc-docsync
configfile: pyproject.toml
plugins: platformdirs-4.12.3, cov-7.1.0
collected 185 items / 159 deselected / 26 selected

tests\test_redact.py ..........................                          [100%]

===================== 26 passed, 159 deselected in 0.32s ======================
```

Command: `coverage`

```text
$ coverage
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
[perf] offline generate best of 3: 0.0113 s (all: 0.0113, 0.0128, 0.0124); target < 1.0 s: target met; hard limit < 2.0 s
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
======================= 455 passed, 1 skipped in 6.12s ========================
```

Command: `ruff check .`

```text
$ ruff check .
All checks passed!
```

Command: `python -m pip_audit`

```text
$ python -m pip_audit
No known vulnerabilities found
Name    Skip Reason
------- ----------------------------------------------------------------------
docsync Dependency not found on PyPI and could not be audited: docsync (0.1.0)
exit=0
```

Command: `git grep secrets`

```text
$ git grep secrets
src/docsync/redact.py:68:    _rule(r"(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,255}", PLACEHOLDER),
src/docsync/redact.py:70:    _rule(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])", PLACEHOLDER),
src/docsync/redact.py:77:    _rule(r"-----BEGIN [A-Z ]{0,40}PRIVATE KEY-----[A-Za-z0-9+/=\r\n]{0,8192}", PLACEHOLDER),
tests/test_cli.py:15:_TOKEN_SHAPED = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
tests/test_cli.py:429:    shaped = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
tests/test_cli.py:456:    shaped = "ghp_A1b2C3d4E5f6G7h8I9j0K1"
tests/test_integration.py:290:    github = "ghp_A1b2C3d4E5f6G7h8I9j0K1L2M3N4O5P6Q7R8"
tests/test_integration.py:291:    aws = "AKIAIOSFODNN7EXAMPLE"
tests/test_integration.py:292:    anthropic = "sk-ant-api03-abcdefghijklmnop1234"
tests/test_redact.py:19:@pytest.mark.parametrize("prefix", ["ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"])
tests/test_redact.py:202:        f"Authorization: Bearer abc ghp_{_BODY} https://u:p@h.io "
tests/test_redact.py:216:    text = f"password=x ghp_{_BODY}"
tests/test_redact.py:224:_GH_TOKEN = "ghp_A1b2C3d4E5f6G7h8I9j0K1L2M3N4O5P6Q7R8"
tests/test_redact.py:242:        "sk-ant-api03-abcdefghijklmnop1234",
tests/test_redact.py:245:        "github_pat_11ABCDEFG0abcdefghijkl_mnopqrstuvwxyz0123456789",
tests/test_redact.py:247:        "AKIAIOSFODNN7EXAMPLE",
tests/test_redact.py:268:        "-----BEGIN RSA PRIVATE KEY-----",
tests/test_redact.py:269:        "-----BEGIN PRIVATE KEY-----",
tests/test_redact.py:270:        "-----BEGIN OPENSSH PRIVATE KEY-----",
tests/test_redact.py:271:        "-----BEGIN EC PRIVATE KEY-----",
tests/test_redact.py:463:        "sk-ant-api03-abcdefghijklmnop1234",
tests/test_redact.py:464:        "AKIAIOSFODNN7EXAMPLE",
tests/test_redact.py:467:        "-----BEGIN PRIVATE KEY-----\nMIIEowIBAAKCAQEAabc+/def==\n-----END PRIVATE KEY-----",
tests/test_redact.py:498:        "ghp_", "sk-ant", "AKIA", "xoxb-", "eyJ", "MIIEow", "abc123def456", "s3cr3t",
tests/test_redact.py:514:    "repeated github prefix": "ghp_" * 5000,
tests/test_redact.py:516:    "repeated pem header": "-----BEGIN PRIVATE KEY-----" * 740,
tests/test_redact.py:820:    "ghp_A1b2C3d4E5f6G7h8I9j0K1", "AKIAIOSFODNN7EXAMPLE", "sk-ant-api03-abcdefghijklmnop1234",
tests/test_redact.py:823:    "Zm9vYmFyQmF6UXV4MTIzNDU2Nzg5MEFCQ0RFRkdISUpLTE1O", "-----BEGIN PRIVATE KEY-----",
tests/test_redact.py:846:    text = "AKIAIOSFODNN7EXAMPLEsk-ant-api03-abcdefghijklmnop1234"
tests/test_redact.py:852:    assert "AKIA" not in once
tests/test_redact.py:874:        "ghp_abcdefghijklmnopqrstuvwxyz",
tests/test_redact.py:875:        "github_pat_abcdefghijklmnopqrstuvwxyz",
tests/test_redact.py:880:        "AKIAABCDEFGHIJKLMNOP",
tests/test_redact.py:901:    text = "-----BEGIN PRIVATE KEY-----\nMIIEowIBAAKCAQEAabcdefghijkl\n-----END PRIVATE KEY-----"
exit=0
```

Command: `git grep NotImplementedError`

```text
$ git grep NotImplementedError
exit=1
```


Secret-scan classification (every match, all in `.py` files; the `:!*.md` filter excludes Markdown):

| Match | Classification |
|---|---|
| `src/docsync/redact.py:68`, `:70`, `:77` | Detection patterns (`gh[pousr]_`/`github_pat_`, `AKIA`, `PRIVATE KEY` header), not credentials |
| `tests/test_cli.py:15`, `:429`, `:456` | Deliberate fake fixture `ghp_A1b2C3d4E5f6G7h8I9j0K1` |
| `tests/test_integration.py:290-292` | Deliberate fake fixtures (GitHub shape, the AWS documentation example id `AKIAIOSFODNN7EXAMPLE`, an `sk-ant-` shaped string) |
| `tests/test_redact.py:19`, `:202`, `:216`, `:224`, `:242`, `:245`, `:247`, `:268-271`, `:463-467`, `:498`, `:514`, `:516`, `:820`, `:823`, `:846`, `:852`, `:874-880`, `:901` | Deliberate fake fixtures, prefix lists and ReDoS inputs; every body is an obvious placeholder or the published AWS example |

The secret-scan grep returned matches only in the files above and returned no match in any other non-Markdown file. No match is real credential material, and none sits in product code other than the detection patterns in `src/docsync/redact.py`. `git grep -n NotImplementedError -- src` returned no match (exit 1).

### 7.8.8 Scratch probe output (verbatim, `probe.py`, outside the repository)

```text
rules 14 13 1
unbounded: []
callable explicit: []
sk                           REDACTED   '[REDACTED]'
ghp                          REDACTED   '[REDACTED]'
github_pat                   REDACTED   '[REDACTED]'
gho                          REDACTED   '[REDACTED]'
ghu                          REDACTED   '[REDACTED]'
ghs                          REDACTED   '[REDACTED]'
ghr                          REDACTED   '[REDACTED]'
AKIA                         REDACTED   '[REDACTED]'
xoxb                         REDACTED   '[REDACTED]'
xoxp                         REDACTED   '[REDACTED]'
jwt                          REDACTED   '[REDACTED]'
pem                          REDACTED   '[REDACTED]-----END PRIVATE KEY-----'
json                         REDACTED   '{"password": [REDACTED]}'
suffixed                     REDACTED   'SECRET_KEY=[REDACTED]'
plural                       REDACTED   'passwords: [REDACTED]'
table                        REDACTED   '| password | [REDACTED] |'
weakkey                      REDACTED   'key=[REDACTED]'
weakkey_json                 REDACTED   '{"key": [REDACTED]}'
-- boundaries --
letters+sk                   UNCHANGED  'abcsk-abcdefghijklmnopqrstuvwxyz'
SK upper                     UNCHANGED  'SK-abcdefghijklmnopqrstuvwxyz'
Sk                           UNCHANGED  'Sk-abcdefghijklmnopqrstuvwxyz'
sk short15                   UNCHANGED  'sk-abcdefghijklmno'
sk 16                        REDACTED   '[REDACTED]'
sk hyphen-split              REDACTED   '[REDACTED]'
sk newline split             UNCHANGED  'sk-abcdefgh\nijklmnopqrstuv'
sk adjacent                  REDACTED   '[REDACTED]'
sk prefixed by hyphen        REDACTED   'my-[REDACTED]'
sk prefixed by underscore    REDACTED   'x_[REDACTED]'
sk prefixed by digit         UNCHANGED  '1sk-abcdefghijklmnopqrstuvwxyz'
sk after colon               REDACTED   'x:[REDACTED]'
ghp short                    UNCHANGED  'ghp_abcdefghijklmnopqrs'
GHP upper                    UNCHANGED  'GHP_abcdefghijklmnopqrstuvwxyz'
ghp after letters            REDACTED   'x[REDACTED]'
akia lower                   UNCHANGED  'akiaabcdefghijklmnop'
AKIA 15                      UNCHANGED  'AKIAABCDEFGHIJKLMNO'
AKIA 17 tail                 UNCHANGED  'AKIAABCDEFGHIJKLMNOPQ'
AKIA prefixed                UNCHANGED  'XAKIAABCDEFGHIJKLMNOP'
xoxb short                   UNCHANGED  'xoxb-abcdefghi'
xoxe                         UNCHANGED  'xoxe-abcdefghijklmnop'
XOXB                         UNCHANGED  'XOXB-abcdefghijklmnop'
jwt short seg                UNCHANGED  'eyJabcdefg.abcdefgh.sig'
jwt 2seg                     REDACTED   '[REDACTED]'
jwt prefixed hyphen          UNCHANGED  'x-eyJabcdefgh.abcdefgh.sig'
pem lower                    UNCHANGED  '-----begin private key-----\nabc\n'
pem RSA                      REDACTED   '[REDACTED]-----END RSA PRIVATE KEY-----'
pem OPENSSH                  REDACTED   '[REDACTED]'
pem ENCRYPTED                REDACTED   '[REDACTED]'
bearer short                 UNCHANGED  'Bearer abcdefg'
bearer 8                     REDACTED   'Bearer [REDACTED]'
password quoted space        REDACTED   'password = [REDACTED]'
token yaml                   REDACTED   'token: [REDACTED]'
apikey                       REDACTED   'apikey=[REDACTED]'
api-key                      REDACTED   'api-key: [REDACTED]'
api_key short                UNCHANGED  'api_key=short'
secretkey                    REDACTED   'client_secret=[REDACTED]'
x-api-key hdr                REDACTED   'x-api-key: [REDACTED]'
key 19                       UNCHANGED  'key=abcdefghijklmnopqrs'
private_key                  UNCHANGED  'private_key=abc'
access_key short             UNCHANGED  'access_key=abc'
password in table sep        REDACTED   '| Password | [REDACTED] |'
password space               UNCHANGED  'password hunter'
password is                  UNCHANGED  'the password is hunter'
max_tokens                   REDACTED   'max_tokens = [REDACTED]'
api_key_value                UNCHANGED  'api_key_value=abc'
tokenizer                    UNCHANGED  'tokenizer: x'
blob lower 60                UNCHANGED  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
blob mixed nodigit           UNCHANGED  'aBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaB'
blob b64url                  UNCHANGED  'aB1-aB1-aB1-aB1-aB1-aB1-aB1-aB1-aB1-aB1-aB1-aB1-aB1-aB1-aB1-'
--- perf ---
a*20000                            len= 20000      3.2 ms
a-*10000=                          len= 20001      3.0 ms
sk-*6600                           len= 19800      0.2 ms
eyJ*6600                           len= 19800      3.1 ms
aA1*6700                           len= 20100      3.4 ms
password_*2200                     len= 19800      6.4 ms
| secret |*2000                    len= 20000      3.7 ms
password="+a*20000                 len= 20010      3.2 ms
Ab1/*5000                          len= 20000      5.6 ms
ghp_*5000                          len= 20000      0.2 ms
AKIA*5000                          len= 20000      3.1 ms
key=*4000                          len= 16000      2.7 ms
-----BEGIN PRIVATE KEY-----*1000   len= 27000      2.8 ms
eyJ..*                             len= 19200      1.4 ms
https://*2000                      len= 25000      4.3 ms
bearer *                           len= 21000      3.4 ms
authorization:*                    len= 22400      1.1 ms
xoxb-*                             len= 20000      0.7 ms
a/*10000                           len= 20000      5.3 ms
worst ms 6.4
```

### 7.8.9 Final verdict for step 6 as a whole

**Approved.**

No in-scope row is `Fail` (Security: Pass with comment; Test Coverage: Pass with comment; DRY Principle: Pass with comment). CR-33 (High) is Resolved. There is no open Blocker or Major finding: the new findings CR-35 to CR-37 are Minor and CR-38 is Info, none blocking. Blocking CR ids: none. No High severity security or correctness defect remains open, so the remediation freeze (RO-4) is not reopened. Items to carry into Known Limitations: CR-35 (replacing the superseded CR-33 row of 7.7.2), CR-38, and the existing deferred rows; CR-36 should be corrected or disclosed at step 7.

This verdict supersedes 7.6 and is the closing verdict for step 6; sections 1 to 7.7 are retained unchanged as the record.

## 7.9 Resolution of CR-36 (documentation correction, not a code change)

Appended after 7.8; nothing above is edited. Recorded the same way as CR-5 (resolved by changing the specification) and CR-28 (resolved by appending a correction).

| CR id | Severity | Status | Evidence | Notes |
|---|---|---|---|---|
| CR-36 | Minor | **Resolved by documentation correction, not a code change** | docs/02-architecture.md section 7, Security Design, the `Redaction` row: the clause "`sk-` keys (only if they contain a digit)" is now "`sk-` keys", and a sentence states the two rule groups; revision history row 1.4 records the correction with its date from git (2026-10-09) | The human approved the correction at the step 6 closing gate and ruled that the remediation freeze blocks discretionary work, not factual errors in graded deliverables. `src/docsync/redact.py` is unchanged (reviewed commit `3487008`). The corrected text says: explicit prefixed credential patterns are redacted on a prefix match alone and do not require mixed case or a digit; the unprefixed base64 blob heuristic requires at least one uppercase letter, one lowercase letter and one digit |

Re-scan after the correction: docs/01 to docs/04 were searched for any other clause that contradicts the post-T22 redactor. No other normative clause was found. Historical task and review records that describe behaviour that was later superseded were reported to the human as candidates and left unchanged, pending the human's decision.

## 7.10 Triage of the candidates from the post-T22 re-scan (CR-39 to CR-41)

Appended after 7.9; nothing above is edited. The human's standing triage rule applies: High severity, any security false negative, or anything that breaks an accepted AC is stopped and brought to the human; Medium that corrupts the generated document in a way V-9 would catch is stopped and brought to the human; everything else is auto-deferred under the remediation freeze and carried verbatim into Known Limitations.

| CR id | Severity | File | Finding | Bucket | Justification for deferral |
|---|---|---|---|---|---|
| CR-39 | Info | docs/04-impl-plan.md, T21 row | The goal text of T21a lists "long camel-case identifiers" and "`sk-` package names" among the structured text it would stop mangling; the shipped redactor does neither (CR-29, CR-35) | Auto-deferred: Info, a statement of task intent in a historical record, no code or generated-document effect | The authoritative status of both items is recorded in 7.7.2 (CR-29) and 7.8.6 (CR-35); the plan row records what was intended at the time |
| CR-40 | Info | docs/04-impl-plan.md, T4 row | The T4 task description says the `key=value` rule applies to `key` among the strong words; the shipped bare-`key` rule needs a token-shaped value of 20 or more characters | Auto-deferred: Info, a historical task description superseded by T20 and T21a | docs/02-architecture.md section 7 (revision 1.4) states the current rules; the T4 row records what T4 did when it was done |
| CR-41 | Info | docs/03-design-review.md, risk register | The risk example that `key=value` redaction "may over-redact benign text (for example `monkey=...`)" no longer happens: a bare `key` now needs a 20 or more character value | Auto-deferred: Info, a review-time risk example in a historical record; the document is not modified after step 3 | The risk was accepted at step 3 and has since been reduced; no behaviour or deliverable is affected |

Status for all three: **Deferred, disclosed as Known Limitation.** None affects the generated document, so V-9 (RO-5) is not engaged. They must reappear verbatim, with severity and justification, in the Known Limitations sections of docs/06-verification.md and docs/07-pr-description.md.

## 8. Revision History

| Version | Date | Event | Commit(s) | Notes |
|---|---|---|---|---|
| 1.0 | 2026-10-08 | Initial review | 03a965c | Verdict `Changes requested`; blocking CR-1 and CR-2; CR-1 to CR-16 recorded. The reviewed commit was 18aa32b (2026-10-07); the review document itself was committed as 03a965c, which `git log` dates 2026-10-08. T21c: the Date column was corrected from 2026-10-07, which came from the human's instructions and not from git, to the value of `git log -1 --format=%cs 03a965c` |
| 1.1 | 2026-10-08 | Remediation | CR-4: 546f4b1, 675750f; skill alignment (CR-5): 2cfa41a; plan amendment: 0446e96; T20: 9e52a1d | CR-4 fixed by changing the behaviour (RO-3); T20 rewrote `src/docsync/redact.py` (CR-1, CR-2, CR-3); CR-5 resolved by aligning the secret-safety skill to the implemented and architecturally documented placeholder |
| 1.2 | 2026-10-08 | Re-review | re-review committed as d8fb7de, reviewing 9e52a1d | Verdict `Approved`; CR-1 to CR-6 Resolved or Accepted; new findings CR-17 to CR-27 (Minor and Info) |
| 1.3 | 2026-10-08 | Final remediation (T21) | Plan: 167d039; CLAUDE.md rule 9: 4bd4fb8; T21a: f837f74; T21b and T21c: the commit that carries this row | CR-17, CR-19, CR-22, CR-23, CR-24, CR-25 and CR-28 resolved; CR-7 to CR-16, CR-18, CR-20, CR-21, CR-26, CR-27 and CR-29 to CR-34 deferred as Known Limitations (7.7.2); remediation freeze (RO-4) in force. Not a new independent review (7.7) |
| 1.4 | 2026-10-09 | Freeze exception (T22) | Plan: 2f68a61 (dated 2026-10-09); T22: 3487008 | CR-33 (High, security false negative) resolved: explicit prefixed credential rules no longer need mixed case or a digit; rules split into `_EXPLICIT_RULES` and `_HEURISTIC_RULES`; real rule count 14; CR-33 removed from the deferred list (7.7.3); RO-5 and RO-6 recorded for step 7 |
| 1.5 | 2026-10-09 | Delta re-review | reviewing 3487008; committed as the commit that carries this row | Independent review of `src/docsync/redact.py` and `tests/test_redact.py` over `9e52a1d..3487008` (Security, Test Coverage, DRY). Closing verdict for step 6: `Approved`; new findings CR-35 to CR-38; CR-36 awaits a human decision (7.7.3). The date is that of the latest commit when the row was written |
| 1.6 | 2026-10-09 | CR-36 closure | the commit that carries this row (follows c416247) | CR-36 resolved by a documentation correction in docs/02-architecture.md (section 7 and revision row 1.4); no code change. Step 6 closed. The date is that of the latest commit when the row was written |
| 1.7 | 2026-10-09 | Triage of CR-39 to CR-41 | the commit that carries this row (follows 535233d) | CR-39, CR-40 and CR-41 (Info) auto-deferred under the human's standing triage rule (7.10); no code or generated-document change. The date is that of the latest commit when the row was written |

---
**Gate:** Approve step 6 and continue? (yes / changes needed)
