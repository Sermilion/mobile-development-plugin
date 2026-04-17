from __future__ import annotations

from pathlib import Path


ORCHESTRATION_PLAYBOOKS: dict[str, str] = {
  "stack-routing": "orchestration/stack-routing/PLAYBOOK.md",
  "review-orchestrator": "orchestration/review-orchestrator/PLAYBOOK.md",
  "review-delegation": "orchestration/review-delegation/PLAYBOOK.md",
  "telemetry-contract": "orchestration/telemetry-contract/PLAYBOOK.md",
  "shell-content-contract": "orchestration/shell-content-contract/PLAYBOOK.md",
}

ADDON_DIRECTORY_NAME = "addons"
ADDON_IMPLEMENTATION_SUFFIX = "-implementation.md"
ADDON_REVIEW_SUFFIX = "-review.md"
ADDON_REPORTING_LINE = "Selected add-ons: none | <add-on slugs>"


def compute_addon_supporting_file_targets(root: Path) -> dict[str, str]:
  """Return the sidecar-target map for governed add-on files (SKILL-17).

  Walks every ``platform-packs/<slug>/`` pack and flattens each
  :class:`AddonDeclaration`'s implementation, review, and topic files
  into a mapping from the file's basename to its repo-relative path. The
  scaffolder and validator consume this map to wire sibling supporting
  files without hardcoding platform names.
  """
  # Import lazily to avoid pulling PyYAML into entry points that only use
  # the non-add-on constants above.
  from skill_bill.shell_content_contract import discover_platform_packs

  targets: dict[str, str] = {}
  packs = discover_platform_packs(root / "platform-packs")
  for pack in packs:
    if not pack.governs_addons:
      continue
    for declaration in pack.declared_addons:
      for file_path in (
        declaration.implementation,
        declaration.review,
        *declaration.topic_files,
      ):
        relative = file_path.relative_to(root)
        targets[file_path.name] = relative.as_posix()
  return targets


_ADDON_SUPPORTING_FILE_TARGETS = compute_addon_supporting_file_targets(
  Path(__file__).resolve().parent.parent
)

SUPPORTING_FILE_TARGETS: dict[str, str] = {
  "stack-routing.md": ORCHESTRATION_PLAYBOOKS["stack-routing"],
  "review-orchestrator.md": ORCHESTRATION_PLAYBOOKS["review-orchestrator"],
  "review-delegation.md": ORCHESTRATION_PLAYBOOKS["review-delegation"],
  "telemetry-contract.md": ORCHESTRATION_PLAYBOOKS["telemetry-contract"],
  "shell-content-contract.md": ORCHESTRATION_PLAYBOOKS["shell-content-contract"],
  **_ADDON_SUPPORTING_FILE_TARGETS,
}

RUNTIME_SUPPORTING_FILES: dict[str, tuple[str, ...]] = {
  "bill-code-review": (
    "stack-routing.md",
    "review-delegation.md",
    "telemetry-contract.md",
    "shell-content-contract.md",
  ),
  "bill-quality-check": ("stack-routing.md", "telemetry-contract.md"),
  "bill-agent-config-quality-check": ("stack-routing.md", "telemetry-contract.md"),
  "bill-go-quality-check": ("stack-routing.md", "telemetry-contract.md"),
  "bill-kotlin-quality-check": ("stack-routing.md", "telemetry-contract.md"),
  "bill-php-quality-check": ("stack-routing.md", "telemetry-contract.md"),
  "bill-agent-config-code-review": ("stack-routing.md", "review-orchestrator.md", "review-delegation.md", "telemetry-contract.md"),
  "bill-kotlin-code-review": ("stack-routing.md", "review-orchestrator.md", "review-delegation.md", "telemetry-contract.md"),
  "bill-backend-kotlin-code-review": ("stack-routing.md", "review-orchestrator.md", "review-delegation.md", "telemetry-contract.md"),
  "bill-kmp-code-review": (
    "stack-routing.md",
    "review-orchestrator.md",
    "review-delegation.md",
    "telemetry-contract.md",
    "android-compose-review.md",
    "android-navigation-review.md",
    "android-interop-review.md",
    "android-design-system-review.md",
    "android-r8-review.md",
    "android-compose-edge-to-edge.md",
    "android-compose-adaptive-layouts.md",
  ),
  "bill-kmp-code-review-ui": (
    "android-compose-review.md",
    "android-navigation-review.md",
    "android-interop-review.md",
    "android-design-system-review.md",
    "android-compose-edge-to-edge.md",
    "android-compose-adaptive-layouts.md",
  ),
  "bill-php-code-review": ("stack-routing.md", "review-orchestrator.md", "review-delegation.md", "telemetry-contract.md"),
  "bill-go-code-review": ("stack-routing.md", "review-orchestrator.md", "review-delegation.md", "telemetry-contract.md"),
  "bill-feature-implement": (
    "telemetry-contract.md",
    "android-compose-implementation.md",
    "android-navigation-implementation.md",
    "android-interop-implementation.md",
    "android-design-system-implementation.md",
    "android-r8-implementation.md",
    "android-compose-edge-to-edge.md",
    "android-compose-adaptive-layouts.md",
  ),
  "bill-feature-verify": ("telemetry-contract.md",),
  "bill-pr-description": ("telemetry-contract.md",),
}

REVIEW_DELEGATION_REQUIRED_SECTIONS = (
  "## GitHub Copilot CLI",
  "## Claude Code",
  "## OpenAI Codex",
  "## GLM",
)

PORTABLE_REVIEW_SKILLS = (
  "bill-agent-config-code-review",
  "bill-kotlin-code-review",
  "bill-backend-kotlin-code-review",
  "bill-kmp-code-review",
  "bill-php-code-review",
  "bill-go-code-review",
)

REVIEW_RUN_ID_PLACEHOLDER = "Review run ID: <review-run-id>"
REVIEW_RUN_ID_FORMAT = "rvw-YYYYMMDD-HHMMSS-XXXX"
REVIEW_SESSION_ID_PLACEHOLDER = "Review session ID: <review-session-id>"
REVIEW_SESSION_ID_FORMAT = "rvs-<uuid4>"
APPLIED_LEARNINGS_PLACEHOLDER = "Applied learnings: none | <learning references>"
RISK_REGISTER_FINDING_FORMAT = "- [F-001] <Severity> | <Confidence> | <file:line> | <description>"
TELEMETRY_OWNERSHIP_HEADING = "Telemetry Ownership"
TRIAGE_OWNERSHIP_HEADING = "Triage Ownership"
PARENT_IMPORT_RULE = (
  "If this review owns the final merged review output for the current review lifecycle, call the "
  "`import_review` MCP tool:"
)
CHILD_NO_IMPORT_RULE = (
  "If this review is delegated or layered under another review, do not call `import_review`."
)
CHILD_METADATA_HANDOFF_RULE = (
  "Return the complete review output plus summary metadata (`review_session_id`, `review_run_id`, "
  "detected scope/stack, execution mode, specialist reviews) to the parent review instead."
)
PARENT_TRIAGE_RULE = (
  "If this review owns the final merged review output for the current review lifecycle and the user "
  "responds to findings, call the `triage_findings` MCP tool:"
)
CHILD_NO_TRIAGE_RULE = (
  "If this review is delegated or layered under another review, do not call `triage_findings`;"
)
NO_FINDINGS_TRIAGE_RULE = "Skip triage recording when the final parent-owned review produced no findings."


TELEMETERABLE_SKILLS: tuple[str, ...] = tuple(
  skill_name
  for skill_name, supporting_files in RUNTIME_SUPPORTING_FILES.items()
  if "telemetry-contract.md" in supporting_files
)

INLINE_TELEMETRY_CONTRACT_MARKERS: tuple[str, ...] = (
  "Standalone-first contract",
  "child_steps aggregation",
  "Graceful degradation",
  "Routers never emit",
)


def skills_requiring_supporting_file(file_name: str) -> tuple[str, ...]:
  return tuple(
    skill_name
    for skill_name, supporting_files in RUNTIME_SUPPORTING_FILES.items()
    if file_name in supporting_files
  )


def governed_addon_slugs_for_stack(stack: str) -> tuple[str, ...]:
  """Return the declared add-on slugs for ``stack``, discovered from the manifest.

  SKILL-17: discovery-driven. Walks ``platform-packs/<stack>/platform.yaml``
  and returns the tuple of ``declared_addons[*].slug`` in manifest order
  when the pack declares ``governs_addons: true``. Returns an empty tuple
  when the pack directory is absent. A malformed manifest is NOT silently
  tolerated — the underlying ``ShellContentContractError`` propagates so the
  loud-fail discipline documented in ``AGENTS.md`` applies here too.
  """
  from skill_bill.shell_content_contract import load_platform_pack

  root = Path(__file__).resolve().parent.parent
  pack_root = root / "platform-packs" / stack
  if not (pack_root / "platform.yaml").is_file():
    return ()
  pack = load_platform_pack(pack_root)
  if not pack.governs_addons:
    return ()
  return tuple(declaration.slug for declaration in pack.declared_addons)


def supporting_file_targets(root: Path) -> dict[str, Path]:
  return {
    file_name: root / relative_path
    for file_name, relative_path in SUPPORTING_FILE_TARGETS.items()
  }
