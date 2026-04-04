from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skill_bill.telemetry.schema import TelemetryEvent, ValidationError, create_event


class TelemetrySchemaTest(unittest.TestCase):

  def test_create_event_with_defaults(self) -> None:
    event = create_event(event_type="code-review-completed", skill="bill-code-review")
    self.assertEqual(event.event_type, "code-review-completed")
    self.assertEqual(event.skill, "bill-code-review")
    self.assertNotEqual(event.event_id, "")
    self.assertNotEqual(event.timestamp, "")
    self.assertEqual(event.repo, "")
    self.assertEqual(event.metadata, {})

  def test_create_event_with_all_fields(self) -> None:
    event = create_event(
      event_type="code-review-completed",
      skill="bill-kotlin-code-review",
      repo="/tmp/test-repo",
      metadata={"findings": 3},
      timestamp="2026-04-04T12:00:00+00:00",
      event_id="test-id-123",
    )
    self.assertEqual(event.event_id, "test-id-123")
    self.assertEqual(event.repo, "/tmp/test-repo")
    self.assertEqual(event.metadata, {"findings": 3})
    self.assertEqual(event.timestamp, "2026-04-04T12:00:00+00:00")

  def test_serialization_roundtrip(self) -> None:
    event = create_event(
      event_type="code-review-completed",
      skill="bill-code-review",
      event_id="roundtrip-id",
      timestamp="2026-04-04T12:00:00+00:00",
    )
    raw = event.to_json()
    restored = TelemetryEvent.from_json(raw)
    self.assertEqual(event, restored)

  def test_rejects_empty_event_type(self) -> None:
    with self.assertRaises(ValidationError):
      create_event(event_type="", skill="bill-code-review")

  def test_rejects_invalid_event_type(self) -> None:
    with self.assertRaises(ValidationError):
      create_event(event_type="Code Review!", skill="bill-code-review")

  def test_rejects_empty_skill(self) -> None:
    with self.assertRaises(ValidationError):
      create_event(event_type="code-review-completed", skill="")

  def test_rejects_invalid_skill_name(self) -> None:
    with self.assertRaises(ValidationError):
      create_event(event_type="code-review-completed", skill="not-a-bill-skill")

  def test_rejects_uppercase_event_type(self) -> None:
    with self.assertRaises(ValidationError):
      create_event(event_type="Code-Review", skill="bill-code-review")


if __name__ == "__main__":
  unittest.main()
