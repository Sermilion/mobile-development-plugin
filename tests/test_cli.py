from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CLITest(unittest.TestCase):

  def test_version(self) -> None:
    result = self.run_cli(["version"])
    self.assertEqual(result.returncode, 0)
    self.assertIn("skill-bill", result.stdout)
    self.assertIn("0.1.0", result.stdout)

  def test_doctor(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      result = self.run_cli(["doctor"], state_dir=temp_dir)
      self.assertEqual(result.returncode, 0)
      self.assertIn("status: ok", result.stdout)
      self.assertIn("outbox size: 0 event(s)", result.stdout)

  def test_help(self) -> None:
    result = self.run_cli(["--help"])
    self.assertEqual(result.returncode, 0)
    self.assertIn("telemetry", result.stdout)
    self.assertIn("version", result.stdout)
    self.assertIn("doctor", result.stdout)

  def test_telemetry_capture_subprocess(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      result = self.run_cli(
        [
          "telemetry", "capture",
          "--event-type", "test-event",
          "--skill", "bill-code-review",
        ],
        state_dir=temp_dir,
      )
      self.assertEqual(result.returncode, 0, result.stderr)

      outbox_file = Path(temp_dir) / "outbox" / "events.jsonl"
      self.assertTrue(outbox_file.exists())
      lines = outbox_file.read_text(encoding="utf-8").splitlines()
      self.assertEqual(len(lines), 1)
      event = json.loads(lines[0])
      self.assertEqual(event["event_type"], "test-event")

  def test_telemetry_flush_dry_run(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      self.run_cli(
        [
          "telemetry", "capture",
          "--event-type", "flush-test",
          "--skill", "bill-code-review",
        ],
        state_dir=temp_dir,
      )

      result = self.run_cli(["telemetry", "flush", "--dry-run"], state_dir=temp_dir)
      self.assertEqual(result.returncode, 0)
      self.assertIn("flush-test", result.stdout)
      self.assertIn("1 event(s)", result.stdout)

  def test_doctor_with_populated_outbox(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      self.run_cli(
        [
          "telemetry", "capture",
          "--event-type", "test-event",
          "--skill", "bill-code-review",
        ],
        state_dir=temp_dir,
      )
      result = self.run_cli(["doctor"], state_dir=temp_dir)
      self.assertEqual(result.returncode, 0)
      self.assertIn("outbox size: 1 event(s)", result.stdout)

  def test_telemetry_flush_with_limit(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      for _ in range(3):
        self.run_cli(
          [
            "telemetry", "capture",
            "--event-type", "test-event",
            "--skill", "bill-code-review",
          ],
          state_dir=temp_dir,
        )
      result = self.run_cli(["telemetry", "flush", "--dry-run", "--limit", "2"], state_dir=temp_dir)
      self.assertEqual(result.returncode, 0)
      self.assertIn("2 event(s)", result.stdout)

  def test_telemetry_flush_empty_outbox(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      result = self.run_cli(["telemetry", "flush", "--dry-run"], state_dir=temp_dir)
      self.assertEqual(result.returncode, 0)
      self.assertIn("empty", result.stdout.lower())

  def run_cli(
    self,
    args: list[str],
    state_dir: str | None = None,
  ) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if state_dir:
      env["SKILL_BILL_STATE_DIR"] = state_dir
    return subprocess.run(
      [sys.executable, "-m", "skill_bill"] + args,
      capture_output=True,
      text=True,
      check=False,
      cwd=str(ROOT),
      env=env,
    )


if __name__ == "__main__":
  unittest.main()
