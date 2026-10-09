# DS-3 — Licence fallback from a LICENSE file

| Field | Value |
|---|---|
| Issue key | DS-3 |
| Type | Story |
| Priority | Low |
| Reporter | Reviewer of PR #1 |
| Source | Known Limitation disclosed in DS-1 verification |
| Depends on | DS-1 |

## User Story

**As a** reviewer reading generated documentation,
**I want** the licence to be reported when the repository ships a `LICENSE` file but does not
declare a licence in `pyproject.toml`,
**so that** the field stops reading `Not Found` for projects that clearly are licensed.

## Problem

DS-1 resolves the licence only from `pyproject.toml`. This repository ships an MIT `LICENSE`
file, yet the generated document reports `License: Not Found`. That was disclosed as a known
limitation in PR #1 and is now being picked up as its own work item.

## Acceptance Criteria

- **AC1** — When `pyproject.toml` declares a licence, that value continues to be used
  unchanged.
- **AC2** — When it declares none but a licence file exists in the repository root, the
  licence is reported from that file.
- **AC3** — When neither source is available, the field still reads `Not Found`.
- **AC4** — A licence file that cannot be understood must not crash the tool.
- **AC5** — The document must remain byte-identical across repeated runs.
- **AC6** — The committed `docs/PROJECT_DOCS.md` must be regenerated and remain in sync.

## Notes / Open Questions from Refinement

- We did not agree which filenames count as a licence file.
- We did not define how the licence name is identified from the file's contents, or how much
  of the file may be read.
- It is unclear whether the document should say where the licence came from.
- The behaviour when both sources disagree was not discussed.

## Out of Scope

- SPDX validation.
- Reading licences from dependencies.
- Changing the hosted licence field, which comes from the platform API.