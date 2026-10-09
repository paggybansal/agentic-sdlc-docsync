
### 📄 `.claude/skills/python-test-standards/SKILL.md`

```markdown
---
name: python-test-standards
description: Mandatory pytest conventions for this repository - naming, AAA structure, fixtures, faking HTTP, and the required edge-case matrix. Use whenever writing or reviewing tests under tests/.
---

# Python Test Standards

## Naming

- Files: `tests/test_<module>.py`
- Tests: `test_<unit>_<condition>_<expected_outcome>`
  e.g. `test_github_collector_timeout_returns_not_found`
- No test may assert more than one behaviour.

## Structure — Arrange / Act / Assert

```python
def test_renderer_missing_version_renders_not_found(tmp_path):
    # Arrange
    facts = ProjectFacts(name="demo", version=None)

    # Act
    markdown = render(facts)

    # Assert
    assert "| Version | Not Found |" in markdown