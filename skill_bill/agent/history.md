## [2026-04-04] runtime-telemetry-skeleton
Areas: skill_bill/, skills/base/bill-code-review/, .github/workflows/, tests/
- Introduced skill_bill/ Python package with CLI entrypoint via pyproject.toml (zero external deps)
- Telemetry pipeline: capture command validates events and writes JSONL to local outbox at $HOME/.skill-bill/outbox/
- Event schema enforces bill-* skill name pattern and lowercase-hyphenated event types
- Outbox read_all silently skips corrupt JSONL lines for resilience
- State directory supports SKILL_BILL_STATE_DIR env override for testability
- bill-code-review SKILL.md documents optional telemetry capture call (reusable)
- CI workflow updated with explicit Python 3.13 setup and pip install -e .
Feature flag: N/A
Acceptance criteria: 12/12 implemented
