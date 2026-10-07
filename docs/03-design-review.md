# Design Review — DS-1 Automated Documentation Sync

| Field | Value |
|---|---|
| Artifact | docs/03-design-review.md |
| SDLC Step | 3 — Design Review |
| Author | design-reviewer |
| Date | 2026-10-07 |
| Status | Draft |

## 1. Review Scope

| Item | Value |
|---|---|
| Documents reviewed | docs/01-requirements.md (Status Draft, authoritative); docs/02-architecture.md as committed in 2523db4 (v1.0), then revised to v1.1 by this review |
| Also consulted | CLAUDE.md |
| Reviewer role | Principal Engineer, design review before any code |
| Date | 2026-10-07 |
| Lenses applied, in order | Correctness, failure modes, security, idempotency/determinism, testability, simplicity, operability |
| Not reviewed | `.env` and other secret files (never read); no code exists yet |

## 2. Requirement Coverage Matrix

Status is for the v1.0 design plus the fixes of this review. Notes name findings that tightened a row.

| ID | Covered by | Status |
|---|---|---|
| FR-1 | C-7 CLI, data flow step 7 | Covered |
| FR-2 | C-6 Renderer, Section 3 content table | Covered |
| FR-3 | C-2 Model, C-4, C-6 (NOT_FOUND sentinel); DR-4 per-field partial payloads | Covered |
| FR-4 | C-5, `hosted` dict with exactly six keys; DR-4 | Covered |
| FR-5 | C-6, Generation Info constants only | Covered |
| FR-6 | C-3 `redact`, called only by C-7; DR-1, DR-2 | Covered |
| FR-7 | C-4 reads only `pyproject.toml` and `.py`; test patches open | Covered |
| FR-8 | C-5, Section 7; DR-2, DR-6 | Covered |
| FR-9 | C-5 `token is None` branch; DR-2 (empty token) | Covered |
| FR-10 | C-5 offline branch, `--offline` wins | Covered |
| FR-11 | C-5, Section 6; DR-4 | Covered |
| FR-12 | C-5 `timeout=5`, no retry; DR-5 caveat | Covered |
| FR-13 | C-2, C-4, C-6 | Covered |
| FR-14 | C-4 | Covered |
| FR-15 | C-7 `check`; DR-7 | Covered |
| FR-16 | C-7 (check never writes) | Covered |
| FR-17 | C-6/C-7; Section 11; DR-3 | Covered |
| FR-18 | C-7, Section 9 | Covered |
| FR-19 | C-1, C-7 catch-all; DR-7 | Covered |
| FR-20 | C-3, C-7 | Covered |
| NFR-1 | G-1, static parsing, perf test; DR-12 (size Not Found) | Covered |
| NFR-2 | G-2, single request; DR-5 (timeout is per phase) | Covered |
| NFR-3 | Section 8 coverage command | Covered |
| NFR-4 | Section 8 naming rule | Covered |
| NFR-5 | G-4, Section 5 | Covered |
| NFR-6 | G-5 | Covered |
| NFR-7 | G-6, autouse fixture in Section 8 | Covered |
| NFR-8 | G-7, Section 11 | Covered |
| NFR-9 | G-8, Section 6 catch-all; DR-7 | Covered |
| NFR-10 | G-9, Section 7; DR-1 | Covered |
| EC-1 | C-5 | Covered |
| EC-2 | C-5 | Covered |
| EC-3 | C-5 | Covered |
| EC-4 | C-5 | Covered |
| EC-5 | C-5 | Covered |
| EC-6 | C-4, C-6 | Covered |
| EC-7 | C-4 | Covered |
| EC-8 | C-4 | Covered |
| EC-9 | C-3 | Covered |
| EC-10 | C-7 | Covered |
| EC-11 | C-7; DR-6 | Covered |
| EC-12 | C-7; DR-7 | Covered |
| EC-13 | C-4 | Covered |
| EC-14 | C-5 | Covered |

Gap rows: none. Two rows (FR-12 and NFR-2) carry a documented residual risk, see DR-5 and Section 6.

## 3. Findings

| ID | Severity | Lens | Finding | Recommendation | Decision | Rationale |
|---|---|---|---|---|---|---|
| DR-1 | High | Security | The redaction pattern list is incomplete. It omits `ghs_`, `ghu_`, `ghr_` token prefixes, `Authorization:` header values, and credentials embedded in URLs (`https://user:pass@host`), which routinely appear in VCS dependency strings and project descriptions that flow into the document. Also, if the token env var is set but empty or whitespace, a literal-value replacement can mangle all text. Ordering of patterns was unspecified. | Extend and order the patterns (literal secrets first, then prefixes, headers, URL userinfo, key=value); ignore empty or whitespace secrets; fixed `[REDACTED]` placeholder; redaction must be idempotent; also apply to `UsageError` messages that echo user input. Tests per pattern. | Accepted | Directly protects FR-6, NFR-10, EC-9 at the single choke point. |
| DR-2 | Medium | Security / Testability | `redact` implicitly reads `DOCSYNC_GITHUB_TOKEN` from the environment. A hidden global makes it impure, harder to unit test, and lets a forgotten call site silently skip the literal-token rule. | Signature `redact(text, secrets=())`; `cli.py` passes the token explicitly. Redactor reads no environment. | Accepted | Pure function is testable with no monkeypatching and keeps FR-8 auditable. |
| DR-3 | High | Idempotency / Determinism | "Sorted" is unspecified (locale vs code point); API `topics` order is not guaranteed; descriptions with newlines, CR or `\|` can break structure; Windows path separators may leak; and git `core.autocrlf` can rewrite the committed file to CRLF so `check` reports false drift on a clean tree. FR-17 and NFR-8 are Must. | Add Section 11: code-point sort for all collections including topics, `/` separators, whitespace and pipe normalisation, single trailing LF, byte-mode I/O, and a `.gitattributes` line `docs/PROJECT_DOCS.md text eol=lf` to be created by the plan. | Accepted | Required to meet FR-15 and FR-17 on the Windows developer environment actually in use. |
| DR-4 | Medium | Failure modes | Only `requests.Timeout`, status codes and `ValueError` are named. `ConnectionError`, SSL and redirect errors would escape as unexpected errors (exit 2) violating FR-11. A valid JSON object with `license: null`, missing keys, empty topics or wrong types (partial response) is unspecified, and a null license is common. | Catch `requests.RequestException` as the base class with fixed per-class text; per-field extraction renders only the affected field as `Not Found`, with no warning when the response itself was valid. | Accepted | Closes a gap between FR-11 and the design without weakening FR-3 or FR-4. |
| DR-5 | Low | Failure modes | `requests` `timeout=5` applies to connect and read phases separately, not as a wall-clock cap, and DNS time is not covered. Worst case may exceed NFR-2's 5 s. | Keep `timeout=5` as FR-12 mandates; document the limitation in the design and carry it as residual risk; mocked-timeout test plus timing in verification. | Accepted | FR-12 fixes the value; a thread-based hard deadline adds complexity not justified by the requirement. |
| DR-6 | Medium | Security / Correctness | `OWNER/NAME` validation is only described as "matches the form". Loose validation allows path segments such as `..` or query characters into the URL path. The API base is not pinned, so any future override could send the bearer token to another host. | Strict pattern `^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$`, neither part `.` or `..`; hard-code `https://api.github.com` with no env or flag override. | Accepted | Prevents token exfiltration and URL injection at zero cost; supports EC-11 and FR-8. |
| DR-7 | Medium | Operability | NFR-9 says exit codes only 0, 1, 2, but `KeyboardInterrupt` and `BrokenPipeError` are not handled (traceback or 130). In `check`, only a missing file should be drift; other read errors (for example `--out` is a directory, permission denied) must not be reported as drift. Drift output gives no next step. | Map `KeyboardInterrupt`/`BrokenPipeError` to exit 2; `check` treats only `FileNotFoundError` as drift, other `OSError` as exit 2; drift line says to run `docsync generate`. | Accepted | Needed for FR-15, FR-19, NFR-9 and actionable CI logs. |
| DR-8 | Low | Simplicity | `Field` is a frozen dataclass wrapping a single `value`; it adds a layer every collector and the renderer must wrap and unwrap. | Delete `Field`; use `FieldValue = str \| tuple[str, ...]` directly with `NOT_FOUND` as the string sentinel. | Accepted | Fewer types, same guarantees. |
| DR-9 | Medium | Correctness | Module scan skip list (OQ-3) is open, which makes Section 4 output depend on the implementer. Scanning `venv`, `build`, `site-packages` would break NFR-1 and pollute output. Test counting rules are vague (class methods, async, files that fail `ast.parse`). | Fix the skip list and symlink rule in Section 11; define test counting; `SyntaxError` file counts as a file, adds one warning (EC-8 style). | Accepted | Removes ambiguity that would otherwise leak into tests and determinism. |
| DR-10 | Low | Operability | OQ-6: should `check` print a diff on drift? Requirements do not ask for it. | No diff; print the one-line hint from DR-7. | Rejected (diff output) | A diff adds scope and a leakage surface; the hint line is enough. |
| DR-11 | Low | Correctness | Suggestion: infer `--github-repo` from `git remote` when omitted, for ease of use. | Do not infer. | Rejected | Contradicts A-2/EC-14; remote URLs may embed credentials and make output environment-dependent. |
| DR-12 | Low | Testability | NFR-1 needs a repository size for the perf measurement, which is Not Found (A-3). | Choose a fixture size in the implementation plan and record it. | Deferred | Value is not derivable now; owned by step 4. |

Severity count: High 2 (DR-1, DR-3), Medium 5 (DR-2, DR-4, DR-6, DR-7, DR-9), Low 5 (DR-5, DR-8, DR-10, DR-11, DR-12). Total 12. Decisions: Accepted 9, Rejected 2 (DR-10, DR-11), Deferred 1 (DR-12). Note: DR-10's hint line is applied; only the diff output is rejected.

## 4. Agreed Design Decisions

| ID | Decision |
|---|---|
| ADD-1 | There is exactly one redaction function, `redact(text, secrets=())`, pure, with the ordered pattern set in architecture Section 7, applied by `cli.py` before every write, comparison and print (DR-1, DR-2). |
| ADD-2 | The API base is hard-coded to `https://api.github.com`; `--github-repo` must match the strict pattern; the token is sent only there (DR-6). |
| ADD-3 | All collections sort by Unicode code point; paths are relative with `/`; scalars are whitespace/pipe normalised; output is UTF-8 LF bytes with one trailing newline (DR-3). |
| ADD-4 | A `.gitattributes` entry forcing LF for `docs/PROJECT_DOCS.md` is part of the deliverable and goes into the implementation plan (DR-3). |
| ADD-5 | Any `requests.RequestException`, non-2xx, bad JSON or non-object payload yields exactly one warning and six `Not Found` fields; a valid response with an individual missing or null field yields only that field `Not Found`, no warning (DR-4). |
| ADD-6 | `check` treats only a missing file as drift; any other I/O error is exit 2; every exit is 0, 1 or 2, including interrupts and broken pipes (DR-7). |
| ADD-7 | The `Field` wrapper is removed (DR-8). |
| ADD-8 | Section content mapping and static test counting (A-1, OQ-1) are as in architecture Section 3, plus DR-9 rules. Human confirmation is still taken at the step 3 gate. |
| ADD-9 | Relative `--out` resolves against the current working directory (OQ-7). |
| ADD-10 | No `git` access and no repository inference (DR-11). No diff output on drift (DR-10). |

## 5. Changes Applied to architecture.md

1. Header status updated; Section 2: C-2 loses `Field` (DR-8); C-3 signature becomes `redact(text, secrets=())` and is declared environment-free (DR-2).
2. Section 3 narrative: strict `--github-repo` pattern (DR-6); hard-coded API base, `RequestException` handling and per-field partial handling (DR-4, DR-6); explicit token passed to redaction (DR-2); byte-mode write, `check` read-error rule, drift hint line (DR-7, DR-10).
3. Section 3 content table: module scan refers to the Section 11 skip list; test counting rules defined (DR-9).
4. Section 4: `Field` replaced by `FieldValue` alias (DR-8).
5. Section 6: EC-1 row covers all `RequestException`; catch-all handles `KeyboardInterrupt` and `BrokenPipeError` (DR-4, DR-7).
6. Section 7: redaction row rewritten with ordered patterns, new prefixes, URL userinfo, empty-secret rule, idempotency (DR-1, DR-2).
7. Section 10: OQ-1 to OQ-3, OQ-5 to OQ-7 given resolutions.
8. New Section 11 "Determinism and Robustness Rules" (DR-3, DR-5, DR-9).
9. New `## Revision History` listing applied DR-ids (v1.1).

## 6. Residual Risks

| Risk | Mitigation |
|---|---|
| Per-phase `requests` timeout may exceed 5 s wall clock in rare cases (NFR-2, DR-5) | Mocked-timeout test; online timing in step 7; report as measured, not assumed |
| Regex redaction cannot catch every secret format (NFR-10) | Single choke point, pattern tests per format, key=value fallback; extend patterns in future |
| `key=value` redaction may over-redact benign text (for example "monkey=...") | Output stays deterministic; accept false positives over leaks |
| Users without `.gitattributes` or with other eol tooling may see false drift (FR-15) | ADD-4 file shipped by this repo; documented in the PR description |
| GitHub API schema or `license` shape change | Per-field extraction yields `Not Found` instead of failing |
| NFR-1 measurement size is Not Found (DR-12) | Fix a fixture size in step 4 and state it in the verification report |

## 7. Review Outcome

**Approved with conditions.**

Conditions:
1. The implementation plan (step 4) must include a task for `.gitattributes` (ADD-4) and a perf fixture size (DR-12).
2. Tests must exist for each redaction pattern in DR-1, the empty-token case, `RequestException` subclasses, partial payloads, `check` read-error exit 2, and the interrupt/broken-pipe mapping.
3. The human confirms OQ-1 and OQ-2 resolutions at the gate.

---
**Gate:** Approve step 3 and continue? (yes / changes needed)
