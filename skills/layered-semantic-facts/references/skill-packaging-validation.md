# Skill Packaging Validation Checklist

Date: 2026-10-26

This checklist is the fallback acceptance method for the Agent Skills packaging requirements. The CI environment does not install or invoke `skills-ref validate`; therefore no official validator pass is claimed.

| Requirement | Evidence | Result |
| --- | --- | --- |
| Frontmatter exists and is YAML-like key/value metadata | `skills/layered-semantic-facts/SKILL.md`; `tests/test_packaging.py::test_skill_metadata_and_layout_follow_agent_skills_constraints` | PASS |
| `name` matches the Skill directory and uses the expected lowercase/hyphen form | `name: layered-semantic-facts` matches directory name | PASS |
| `description` is present, explains what the Skill does and when to use it, and is within 1024 characters | SKILL.md frontmatter; packaging test length assertion | PASS |
| `compatibility` declares Python/runtime/filesystem requirements | SKILL.md frontmatter | PASS |
| Body remains under 500 lines with details in references/scripts | packaging test line count and directory checks | PASS |
| Required `scripts/`, `assets/`, `references/` layout and dependency file exist | packaging test | PASS |
| Runtime paths are derived from installed module locations, not the development repository root | CLI and repository schema-root resolution; copied-install test | PASS |
| Copy only the Skill directory and run scan/query without repository-relative runtime files | `tests/test_packaging.py::test_copied_skill_scans_python_and_rust_then_queries_without_repo_paths`; CI run https://github.com/vchs6/code2semantics/actions/runs/40268487627 | PASS |
| Full product acceptance is distinct from packaging validation | product delivery gate remains BLOCKED; S1–S12 not yet complete | PASS (boundary correctly enforced) |

## Limitations

- The copied-install test validates Python/Rust syntax-inventory scanning and repository-backed query projection. It does not prove the complete tool research/execution, induction-provider, multi-layer semantic construction, or all S1–S12 scenarios.
- Official `skills-ref validate` has not been run; this checklist is the documented fallback, not a claim of official validation.
