# DS-2 — Documentation Freshness Report

| Field | Value |
|---|---|
| Issue key | DS-2 |
| Type | Story |
| Epic | Developer Experience / Agentic SDLC |
| Priority | Medium |
| Reporter | Tech Lead |
| Assignee | Parag Bansal |
| Status | To Do |
| Source | Local ticket file (stands in for JIRA/Confluence) |
| Depends on | DS-1 (docsync generate / check) |

## User Story

**As a** tech lead reviewing pull requests across several repositories,
**I want** a single score telling me how complete a project's generated documentation is,
**so that** I can block merges on documentation that is mostly empty instead of reading
every generated file myself.

## Problem

DS-1 made documentation accurate, but not necessarily *useful*. A project with no
description, no dependencies declared and no tests produces a document where nearly every
field reads `Not Found` — technically in sync, practically worthless. Reviewers currently
have to open the document and eyeball it. There is no number, no threshold, and nothing CI
can gate on.

## Scope

A new read-only subcommand that scores the generated documentation and can fail a build.

## Acceptance Criteria

- **AC1** — A new `report` subcommand prints a completeness score for the project's
  documentation.
- **AC2** — The score reflects how many documentation fields were resolved versus how many
  read `Not Found`.
- **AC3** — Reviewers can set a minimum acceptable score, and the command must fail when the
  project falls below it.
- **AC4** — The report must say *which* fields are missing, not just give a number.
- **AC5** — The command must work with no network access.
- **AC6** — Running the command must never modify any file.
- **AC7** — The same project scored twice in a row must give the same score.

## Non-Functional Expectations

- Must be usable in CI.
- Must not slow the existing commands down.
- Must reuse the existing collectors rather than re-reading the repository differently.
- Must keep the existing secret-handling guarantees.

## Notes / Open Questions from Refinement

- We did not agree how the score is calculated or whether all fields weigh the same.
- We did not define the output format, or whether machine-readable output is needed.
- The default threshold was not discussed.
- Nobody specified the exit code for "below threshold".
- It is unclear whether hosted fields should count when running offline, since they are
  always `Not Found` in that mode.

## Out of Scope

- Scoring more than one repository per run.
- Storing or trending scores over time.
- Changing anything about `generate` or `check` output.