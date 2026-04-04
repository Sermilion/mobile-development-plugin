from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skill_bill.telemetry.schema import create_event
from skill_bill.telemetry.outbox import append, read_all, clear


class TelemetryOutboxTest(unittest.TestCase):

  def test_append_creates_outbox_file(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      outbox_dir = Path(temp_dir) / "outbox"
      event = create_event(event_type="test-event", skill="bill-code-review")
      append(event, outbox_dir)
      self.assertTrue((outbox_dir / "events.jsonl").exists())

  def test_append_writes_valid_jsonl(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      outbox_dir = Path(temp_dir) / "outbox"
      event = create_event(event_type="test-event", skill="bill-code-review", event_id="id-1")
      append(event, outbox_dir)

      lines = (outbox_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
      self.assertEqual(len(lines), 1)
      parsed = json.loads(lines[0])
      self.assertEqual(parsed["event_id"], "id-1")
      self.assertEqual(parsed["event_type"], "test-event")

  def test_append_preserves_existing_events(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      outbox_dir = Path(temp_dir) / "outbox"
      event1 = create_event(event_type="first", skill="bill-code-review", event_id="id-1")
      event2 = create_event(event_type="second", skill="bill-code-review", event_id="id-2")
      append(event1, outbox_dir)
      append(event2, outbox_dir)

      lines = (outbox_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
      self.assertEqual(len(lines), 2)
      self.assertEqual(json.loads(lines[0])["event_id"], "id-1")
      self.assertEqual(json.loads(lines[1])["event_id"], "id-2")

  def test_read_all_returns_all_events(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      outbox_dir = Path(temp_dir) / "outbox"
      event1 = create_event(event_type="first", skill="bill-code-review", event_id="id-1")
      event2 = create_event(event_type="second", skill="bill-code-review", event_id="id-2")
      append(event1, outbox_dir)
      append(event2, outbox_dir)

      events = read_all(outbox_dir)
      self.assertEqual(len(events), 2)
      self.assertEqual(events[0].event_id, "id-1")
      self.assertEqual(events[1].event_id, "id-2")

  def test_read_all_returns_empty_for_missing_file(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      outbox_dir = Path(temp_dir) / "outbox"
      events = read_all(outbox_dir)
      self.assertEqual(events, [])

  def test_clear_removes_all_events(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      outbox_dir = Path(temp_dir) / "outbox"
      event = create_event(event_type="test-event", skill="bill-code-review")
      append(event, outbox_dir)
      append(event, outbox_dir)

      count = clear(outbox_dir)
      self.assertEqual(count, 2)
      self.assertEqual(read_all(outbox_dir), [])


if __name__ == "__main__":
  unittest.main()
