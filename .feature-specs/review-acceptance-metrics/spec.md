# Feature: review-acceptance-metrics
Created: 2026-04-02
Status: Complete
Sources: chat discussion about measuring review acceptance for code-review findings

## Acceptance Criteria
1. Add stable `review_run_id` output to code-review runs and stable `finding_id` output per finding.
2. Add a small local telemetry store for review measurement using SQLite, with a schema for review runs, findings, and review-feedback events.
3. Add a small helper CLI/workflow in this repo that records explicit review feedback events such as accepted, dismissed, and fix-requested findings.
4. Keep the measurement system local-first and portable across agent runtimes; do not require a cloud backend for the first version.
5. Add documentation describing how review measurements are recorded and how to inspect/query them.
6. Add tests for the telemetry schema/writer logic and the review-output contract changes needed for IDs.

## Non-Goals
- Datadog or Firebase integration
- Automatic cloud sync
- Implicit NLP-based acceptance detection
- Full dashboards

---

## Consolidated Spec

Introduce a first local-first measurement layer for `bill-code-review` and the stack-specific review skills it routes to. The goal is to create a practical baseline metric for review usefulness by tracking how many emitted findings are later accepted, dismissed, or marked as fix-requested by the user.

Every review run should include a stable `review_run_id`, and every finding should include a stable `finding_id` that is unique within that run. These IDs do not need to be globally meaningful beyond the review workflow, but they must be explicit and consistent enough that a follow-up helper can record user feedback against them.

Add a repo-native helper CLI implemented in the current repository. The helper should store review telemetry locally in SQLite and support an explicit workflow for importing a review run and recording user feedback events. The first version should focus on explicit events rather than trying to infer user intent from freeform chat.

The telemetry system must stay portable across agent runtimes. The skills define the output contract and terminology, but the event-writing logic should live in a small helper script rather than depending on agent-specific hooks or third-party telemetry products.

Document the local workflow clearly, including where the database lives by default, how to import a review run, how to record accepted or dismissed findings, and how to inspect summary statistics.
