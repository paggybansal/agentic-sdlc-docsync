---
name: sdlc-doc-templates
description: Canonical structure, heading order and formatting rules for every Agentic SDLC artifact (requirements, architecture, design review, implementation plan, code review, verification, PR description). Use whenever creating or updating a file under docs/.
---

# SDLC Document Templates

## Universal rules

- Every artifact starts with `# <Title> — DS-1 <Work item name>`.
- Second block is always a metadata table:
  `| Field | Value |` with rows: Artifact, SDLC Step, Source documents, Author (agent name),
  Date, Status (`Draft` / `Approved`).
- Use `##` for numbered top-level sections in the exact order given by the owning agent.
- Prefer **tables over prose**. Every row that asserts something must carry evidence or an ID.
- IDs are stable and never renumbered: `FR-n`, `NFR-n`, `EC-n`, `DR-n`, `ADD-n`, `Tn`,
  `CR-n`, `V-n`, `V-DEF-n`.
- Unknown values are written as the literal `Not Found`. Never leave a cell blank.
- Fence all command output in ```text blocks and keep it verbatim.
- Diagrams use Mermaid fenced as ```mermaid.
- End every artifact with:
  `---` then `**Gate:** Approve step <N> and continue? (yes / changes needed)`

## Requirement row template

| ID | Requirement | Source AC | Priority | Acceptance test |
|----|-------------|-----------|----------|-----------------|
| FR-1 | The CLI shall ... | AC1 | Must | `tests/test_x.py::test_y` |

Write requirements as "The system shall <observable behaviour>". Forbidden words:
fast, secure, robust, user-friendly, efficient — replace each with a measurable target.

## Evidence block template

```text
$ <command>
<verbatim output>