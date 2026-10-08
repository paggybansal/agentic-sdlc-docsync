
### 📄 `.claude/skills/secret-safety/SKILL.md`

```markdown
---
name: secret-safety
description: Rules and redaction patterns for keeping credentials out of code, logs, generated documents and git history. Use when writing config handling, output rendering, reviewing code, or verifying the generated document.
---

# Secret Safety

## Hard rules

1. Never read, create or modify: `.env`, `.env.local`, `*.pem`, `*.key`, `*.p12`,
   `secrets.*`, `credentials.*`, `id_rsa*`. Only `.env.example` with **empty** values is allowed.
   A `PreToolUse` hook enforces this and will deny the write.
2. Configuration is read **only** from environment variables via `os.environ.get`.
3. Never print, log, or include an environment variable's **value**. Report only
   `set` / `not set`, e.g. `token: not set -> running in offline mode`.
4. Exception messages must never embed a token or a full request URL containing one.
   Build messages from the host and status code only.
5. Never commit real credentials. If one is ever committed, stop and tell the human to
   rotate it — do not attempt to rewrite history silently.

## Redaction patterns

Any string matching these must be replaced with `[REDACTED]` (the canonical placeholder, as in
docs/02-architecture.md and the tests) before it is written to a document or printed:
sk-[A-Za-z0-9_-]{16,} # Anthropic / OpenAI style
ghp_[A-Za-z0-9]{20,} # GitHub classic PAT
github_pat_[A-Za-z0-9_]{20,} # GitHub fine-grained PAT
gh[pousr]_[A-Za-z0-9_]{20,} # other GitHub tokens
AKIA[0-9A-Z]{16} # AWS access key id
xox[baprs]-[A-Za-z0-9-]{10,} # Slack
eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}(\.[A-Za-z0-9_-]*)? # JWT (header.payload[.signature])
-----BEGIN [A-Z ]*PRIVATE KEY-----
[A-Za-z0-9+/]{40,}={0,2} # long base64 blob: redacted only if it contains at least one uppercase letter, one lowercase
# letter and one digit (a heuristic: plain hex such as a SHA-256 is left alone; the
# implementation uses bounded quantifiers)


The forms above are illustrative of what must be caught. `src/docsync/redact.py` (`_RULES`) is authoritative
and bounds every quantifier (for example `{16,255}` where this list shows `{16,}`).

Redaction is **one shared function**, applied at the single CLI choke point before any text is
written to disk or printed; no other module calls the redactor — duplicating it is a DRY violation and will be flagged in code review.

## Verification

- `git grep -nE "(sk-ant|ghp_|github_pat|AKIA|BEGIN .*PRIVATE KEY)" -- . ":!*.md"` → matches only in `src/docsync/redact.py` (the detection patterns)
  and `tests/` (deliberate fake fixtures); a match anywhere else is a finding
- `docs/PROJECT_DOCS.md` contains no secret-shaped string
- `git status` never shows `.env` as tracked or staged
- A test must prove redaction: feed a fake `ghp_` value in and assert `[REDACTED]` out