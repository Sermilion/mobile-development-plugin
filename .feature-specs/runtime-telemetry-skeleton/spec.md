# Feature: runtime-telemetry-skeleton
Created: 2026-04-04
Status: Complete
Sources: inline design doc (Skill Bill runtime + telemetry plan)

## Acceptance Criteria
1. Repo has a pyproject.toml with a PEP 621 package manifest and skill-bill CLI entrypoint
2. skill_bill/ Python package exists with config, state directory, and telemetry modules
3. skill-bill telemetry capture writes validated events to a local JSONL outbox
4. skill-bill telemetry flush reads the outbox (stub — no network transport in v1)
5. skill-bill doctor and skill-bill version commands exist with basic output
6. Event schema validates event-type, skill name, and auto-generates ID + timestamp
7. File-backed outbox at $HOME/.skill-bill/outbox/events.jsonl with append-safe writes
8. bill-code-review SKILL.md documents how to emit a telemetry event via the CLI
9. Tests cover outbox writing, capture validation, CLI behavior, and schema
10. CI workflow updated to install the package before running tests
11. .gitignore updated for Python build artifacts
12. Existing validation (validate_agent_configs.py, agnix, tests) continues to pass
