from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_metrics  # noqa: E402


SAMPLE_REVIEW = """\
Routed to: bill-agent-config-code-review
Review run ID: rvw-20260402-001
Detected review scope: unstaged changes
Detected stack: agent-config
Signals: README.md, install.sh
Execution mode: inline
Reason: agent-config signals dominate

### 2. Risk Register
- [F-001] Major | High | README.md:12 | README wording is stale after the routing change.
- [F-002] Minor | Medium | install.sh:88 | Installer prompt wording is inconsistent with the new flow.
"""


class ReviewMetricsTest(unittest.TestCase):
  def test_import_review_creates_run_and_findings(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      db_path = Path(temp_dir) / "metrics.db"
      review_path = Path(temp_dir) / "review.txt"
      review_path.write_text(SAMPLE_REVIEW, encoding="utf-8")

      result = self.run_cli(
        ["--db", str(db_path), "import-review", str(review_path), "--format", "json"]
      )

      self.assertEqual(result["exit_code"], 0, result["stderr"])
      payload = json.loads(result["stdout"])
      self.assertEqual(payload["review_run_id"], "rvw-20260402-001")
      self.assertEqual(payload["finding_count"], 2)
      self.assertEqual(payload["routed_skill"], "bill-agent-config-code-review")

  def test_record_feedback_and_stats_report_acceptance_rate(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      db_path = Path(temp_dir) / "metrics.db"
      review_path = Path(temp_dir) / "review.txt"
      review_path.write_text(SAMPLE_REVIEW, encoding="utf-8")

      import_result = self.run_cli(
        ["--db", str(db_path), "import-review", str(review_path), "--format", "json"]
      )
      self.assertEqual(import_result["exit_code"], 0, import_result["stderr"])

      accepted = self.run_cli(
        [
          "--db",
          str(db_path),
          "record-feedback",
          "--run-id",
          "rvw-20260402-001",
          "--event",
          "accepted",
          "--finding",
          "F-001",
          "--format",
          "json",
        ]
      )
      self.assertEqual(accepted["exit_code"], 0, accepted["stderr"])

      fix_requested = self.run_cli(
        [
          "--db",
          str(db_path),
          "record-feedback",
          "--run-id",
          "rvw-20260402-001",
          "--event",
          "fix_requested",
          "--finding",
          "F-001",
          "--finding",
          "F-002",
          "--format",
          "json",
        ]
      )
      self.assertEqual(fix_requested["exit_code"], 0, fix_requested["stderr"])

      stats = self.run_cli(
        ["--db", str(db_path), "stats", "--run-id", "rvw-20260402-001", "--format", "json"]
      )
      self.assertEqual(stats["exit_code"], 0, stats["stderr"])

      payload = json.loads(stats["stdout"])
      self.assertEqual(payload["total_findings"], 2)
      self.assertEqual(payload["accepted_findings"], 1)
      self.assertEqual(payload["fix_requested_findings"], 2)
      self.assertEqual(payload["actionable_findings"], 2)
      self.assertEqual(payload["acceptance_rate"], 1.0)

  def test_import_review_rejects_missing_review_run_id(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      db_path = Path(temp_dir) / "metrics.db"
      review_path = Path(temp_dir) / "review.txt"
      review_path.write_text(
        SAMPLE_REVIEW.replace("Review run ID: rvw-20260402-001\n", ""),
        encoding="utf-8",
      )

      result = self.run_cli(
        ["--db", str(db_path), "import-review", str(review_path), "--format", "json"]
      )

      self.assertEqual(result["exit_code"], 1)
      self.assertIn("Review output is missing 'Review run ID", result["stderr"])

  def run_cli(self, argv: list[str]) -> dict[str, str | int]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
      exit_code = review_metrics.main(argv)
    return {
      "exit_code": exit_code,
      "stdout": stdout.getvalue(),
      "stderr": stderr.getvalue(),
    }


if __name__ == "__main__":
  unittest.main()
