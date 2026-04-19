"""SKILL-21 AC 15(c): migration script coverage.

The migration script rewrites governed SKILL.md files under shelled
families, moves author prose into a new sibling ``content.md``, and
regenerates the shell. Tests here exercise idempotency, byte-match
(``--strict``), per-skill rollback on validator failure, the automatic
``_migration_backup/<timestamp>/`` directory, and the summary + exit
codes.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


import migrate_to_content_md  # noqa: E402
from skill_bill.shell_content_contract import InvalidExecutionSectionError  # noqa: E402


KOTLIN_MANIFEST = """\
platform: kotlin
contract_version: "1.0"
display_name: Kotlin
governs_addons: false

routing_signals:
  strong:
    - ".kt"
  tie_breakers: []
  addon_signals: []

declared_code_review_areas:
  - architecture

declared_files:
  baseline: code-review/bill-kotlin-code-review/SKILL.md
  areas:
    architecture: code-review/bill-kotlin-code-review-architecture/SKILL.md
"""

V1_0_SKILL_MD = """\
---
name: bill-kotlin-code-review
description: Fixture legacy shell.
---

## Description
Author-edited Kotlin review description.

## Specialist Scope
Fixture specialist scope.

## Inputs
Fixture inputs.

## Outputs Contract
Fixture outputs contract.

## Execution Mode Reporting
Fixture execution mode reporting.

## Telemetry Ceremony Hooks
Fixture telemetry hooks.

## Free Form Setup
This section carries the author's free-form body that must move to
content.md after migration.

## Second Free Form
Another author-owned section.
"""

V1_0_AREA_SKILL_MD = """\
---
name: bill-kotlin-code-review-architecture
description: Fixture legacy area.
---

## Description
Use when reviewing Kotlin architecture.

## Specialist Scope
Fixture specialist scope.

## Inputs
Fixture inputs.

## Outputs Contract
Fixture outputs contract.

## Execution Mode Reporting
Fixture execution mode reporting.

## Telemetry Ceremony Hooks
Fixture telemetry hooks.

## Free Form Only
Author's free-form body.
"""


def _seed_v1_0_kotlin_repo(tmp_path: Path) -> Path:
  repo = tmp_path / "repo"
  repo.mkdir(parents=True)
  (repo / "skills").mkdir()
  pack = repo / "platform-packs" / "kotlin"
  pack.mkdir(parents=True)
  (pack / "platform.yaml").write_text(KOTLIN_MANIFEST, encoding="utf-8")

  baseline = pack / "code-review" / "bill-kotlin-code-review"
  baseline.mkdir(parents=True)
  (baseline / "SKILL.md").write_text(V1_0_SKILL_MD, encoding="utf-8")

  area = pack / "code-review" / "bill-kotlin-code-review-architecture"
  area.mkdir(parents=True)
  (area / "SKILL.md").write_text(V1_0_AREA_SKILL_MD, encoding="utf-8")
  return repo


class MigrationCoverageTest(unittest.TestCase):
  maxDiff = None

  def setUp(self) -> None:
    self._tmpdir = tempfile.TemporaryDirectory()
    self.addCleanup(self._tmpdir.cleanup)
    self.tmp_path = Path(self._tmpdir.name)
    self.repo = _seed_v1_0_kotlin_repo(self.tmp_path)

  def test_migration_moves_free_form_into_content_md(self) -> None:
    report = migrate_to_content_md.migrate(
      self.repo, force=False, strict=False, yes=True
    )
    successes = [entry for entry in report.migrations if entry.status == "migrated"]
    self.assertEqual(len(successes), 2)
    baseline_content = (
      self.repo
      / "platform-packs"
      / "kotlin"
      / "code-review"
      / "bill-kotlin-code-review"
      / "content.md"
    ).read_text(encoding="utf-8")
    self.assertIn("Free Form Setup", baseline_content)
    self.assertIn("Second Free Form", baseline_content)
    # Author-edited Description must also flow into content.md because the
    # body differs from the scaffolder default.
    self.assertIn(
      "Author-edited Kotlin review description",
      baseline_content,
    )

  def test_migration_is_idempotent_second_run_skips(self) -> None:
    first = migrate_to_content_md.migrate(
      self.repo, force=False, strict=False, yes=True
    )
    self.assertTrue(any(entry.status == "migrated" for entry in first.migrations))
    second = migrate_to_content_md.migrate(
      self.repo, force=False, strict=False, yes=True
    )
    self.assertTrue(
      all(entry.status == "skipped" for entry in second.migrations),
      [entry.status for entry in second.migrations],
    )

  def test_force_overwrites_existing_content_md(self) -> None:
    migrate_to_content_md.migrate(
      self.repo, force=False, strict=False, yes=True
    )
    # Mutate content.md out-of-band; --force should overwrite.
    content_path = (
      self.repo
      / "platform-packs"
      / "kotlin"
      / "code-review"
      / "bill-kotlin-code-review"
      / "content.md"
    )
    content_path.write_text("OUT-OF-BAND CONTENT\n", encoding="utf-8")
    report = migrate_to_content_md.migrate(
      self.repo, force=True, strict=False, yes=True
    )
    self.assertTrue(any(entry.status == "migrated" for entry in report.migrations))
    # Force re-writes content.md from the current SKILL.md shape.
    new_body = content_path.read_text(encoding="utf-8")
    self.assertNotEqual(new_body.strip(), "OUT-OF-BAND CONTENT")

  def test_backup_directory_created_before_first_rewrite(self) -> None:
    report = migrate_to_content_md.migrate(
      self.repo, force=False, strict=False, yes=True
    )
    self.assertIsNotNone(report.backup_dir)
    backup_dir = report.backup_dir
    self.assertTrue(backup_dir.is_dir())
    # At least one SKILL.md backup should exist under the backup tree.
    backups = list(backup_dir.rglob("SKILL.md"))
    self.assertGreaterEqual(len(backups), 2)

  def test_per_skill_rollback_on_validator_failure(self) -> None:
    # Patch assert_execution_body_matches for the baseline only to simulate
    # a per-skill validation failure. The area skill should still migrate.
    original = migrate_to_content_md.assert_execution_body_matches

    def selective_asserter(skill_file: Path, *, context_label: str) -> None:
      if "bill-kotlin-code-review/" in str(skill_file):
        raise InvalidExecutionSectionError(
          f"simulated failure for {skill_file}"
        )
      return original(skill_file, context_label=context_label)

    with mock.patch.object(
      migrate_to_content_md,
      "assert_execution_body_matches",
      side_effect=selective_asserter,
    ):
      report = migrate_to_content_md.migrate(
        self.repo, force=False, strict=False, yes=True
      )

    statuses = {entry.skill_name: entry.status for entry in report.migrations}
    self.assertEqual(statuses["bill-kotlin-code-review"], "failed")
    self.assertEqual(statuses["bill-kotlin-code-review-architecture"], "migrated")

    # The baseline SKILL.md should be byte-identical to the v1.0 fixture
    # because its migration rolled back.
    baseline_skill = (
      self.repo
      / "platform-packs"
      / "kotlin"
      / "code-review"
      / "bill-kotlin-code-review"
      / "SKILL.md"
    )
    self.assertEqual(baseline_skill.read_text(encoding="utf-8"), V1_0_SKILL_MD)
    # content.md should NOT have been left behind.
    self.assertFalse(
      (baseline_skill.parent / "content.md").exists(),
      "content.md should have been rolled back with SKILL.md",
    )

  def test_final_summary_and_nonzero_exit_on_failure(self) -> None:
    original = migrate_to_content_md.assert_execution_body_matches

    def always_fail(skill_file: Path, *, context_label: str) -> None:
      raise Exception("simulated global failure")

    with mock.patch.object(
      migrate_to_content_md,
      "assert_execution_body_matches",
      side_effect=always_fail,
    ):
      code = migrate_to_content_md.main(["--yes", "--repo-root", str(self.repo)])
    self.assertNotEqual(code, 0)
    _ = original

  def test_strict_mode_treats_byte_diff_as_edit(self) -> None:
    # Even with strict mode enabled, migration should still succeed because
    # the free-form sections and author-edited description always move into
    # content.md.
    report = migrate_to_content_md.migrate(
      self.repo, force=False, strict=True, yes=True
    )
    self.assertTrue(any(entry.status == "migrated" for entry in report.migrations))


if __name__ == "__main__":
  unittest.main()
