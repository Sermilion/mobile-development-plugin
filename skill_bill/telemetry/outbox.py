from __future__ import annotations

import json
from pathlib import Path

from skill_bill.telemetry.schema import TelemetryEvent


OUTBOX_FILE = "events.jsonl"


def append(event: TelemetryEvent, outbox_dir: Path) -> None:
  outbox_dir.mkdir(parents=True, exist_ok=True)
  outbox_file = outbox_dir / OUTBOX_FILE
  with open(outbox_file, "a", encoding="utf-8") as f:
    f.write(event.to_json() + "\n")


def read_all(outbox_dir: Path) -> list[TelemetryEvent]:
  outbox_file = outbox_dir / OUTBOX_FILE
  if not outbox_file.exists():
    return []

  events: list[TelemetryEvent] = []
  for line in outbox_file.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
      continue
    try:
      events.append(TelemetryEvent.from_json(line))
    except (json.JSONDecodeError, TypeError):
      continue
  return events


def clear(outbox_dir: Path) -> int:
  outbox_file = outbox_dir / OUTBOX_FILE
  if not outbox_file.exists():
    return 0

  events = read_all(outbox_dir)
  count = len(events)
  outbox_file.write_text("", encoding="utf-8")
  return count
