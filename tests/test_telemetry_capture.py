from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skill_bill.telemetry.capture import register, run
from skill_bill.telemetry.outbox import read_all


def make_args(**kwargs) -> argparse.Namespace:
  defaults = {
    "event_type": "code-review-completed",
    "skill": "bill-code-review",
    "repo": "",
    "metadata": "{}",
    "timestamp": None,
  }
  defaults.update(kwargs)
  return argparse.Namespace(**defaults)


class TelemetryCaptureTest(unittest.TestCase):

  def test_capture_valid_event(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      state = Path(temp_dir)
      with mock.patch("skill_bill.telemetry.capture.state_dir", return_value=state):
        exit_code = run(make_args())
      self.assertEqual(exit_code, 0)
      events = read_all(state / "outbox")
      self.assertEqual(len(events), 1)
      self.assertEqual(events[0].event_type, "code-review-completed")

  def test_capture_rejects_invalid_event_type(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      state = Path(temp_dir)
      with mock.patch("skill_bill.telemetry.capture.state_dir", return_value=state):
        exit_code = run(make_args(event_type="INVALID!"))
      self.assertEqual(exit_code, 1)
      events = read_all(state / "outbox")
      self.assertEqual(len(events), 0)

  def test_capture_rejects_invalid_skill_name(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      state = Path(temp_dir)
      with mock.patch("skill_bill.telemetry.capture.state_dir", return_value=state):
        exit_code = run(make_args(skill="not-a-bill"))
      self.assertEqual(exit_code, 1)

  def test_capture_auto_generates_event_id(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      state = Path(temp_dir)
      with mock.patch("skill_bill.telemetry.capture.state_dir", return_value=state):
        run(make_args())
      events = read_all(state / "outbox")
      self.assertTrue(len(events[0].event_id) > 0)

  def test_capture_auto_generates_timestamp(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      state = Path(temp_dir)
      with mock.patch("skill_bill.telemetry.capture.state_dir", return_value=state):
        run(make_args())
      events = read_all(state / "outbox")
      self.assertTrue(len(events[0].timestamp) > 0)

  def test_capture_accepts_custom_metadata(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      state = Path(temp_dir)
      metadata = json.dumps({"routed_to": "bill-kotlin-code-review", "findings": 5})
      with mock.patch("skill_bill.telemetry.capture.state_dir", return_value=state):
        exit_code = run(make_args(metadata=metadata))
      self.assertEqual(exit_code, 0)
      events = read_all(state / "outbox")
      self.assertEqual(events[0].metadata["routed_to"], "bill-kotlin-code-review")
      self.assertEqual(events[0].metadata["findings"], 5)

  def test_capture_rejects_invalid_metadata_json(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      state = Path(temp_dir)
      with mock.patch("skill_bill.telemetry.capture.state_dir", return_value=state):
        exit_code = run(make_args(metadata="not json"))
      self.assertEqual(exit_code, 1)

  def test_capture_rejects_non_object_metadata(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      state = Path(temp_dir)
      with mock.patch("skill_bill.telemetry.capture.state_dir", return_value=state):
        exit_code = run(make_args(metadata="[1,2,3]"))
      self.assertEqual(exit_code, 1)


if __name__ == "__main__":
  unittest.main()
