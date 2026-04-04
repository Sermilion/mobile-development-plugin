from __future__ import annotations

import argparse
import json

from skill_bill.config import state_dir
from skill_bill.telemetry.schema import ValidationError, create_event
from skill_bill.telemetry.outbox import append


def register(subparsers: argparse._SubParsersAction) -> None:
  parser = subparsers.add_parser("capture", help="Capture a telemetry event to the local outbox")
  parser.add_argument("--event-type", required=True, help="Event type (e.g. code-review-completed)")
  parser.add_argument("--skill", required=True, help="Skill name (e.g. bill-code-review)")
  parser.add_argument("--repo", default="", help="Repository path or identifier")
  parser.add_argument("--metadata", default="{}", help="JSON object with additional event data")
  parser.add_argument("--timestamp", default=None, help="ISO 8601 timestamp (auto-generated if omitted)")
  parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
  try:
    metadata = json.loads(args.metadata)
  except json.JSONDecodeError as e:
    print(f"Error: invalid metadata JSON: {e}")
    return 1

  if not isinstance(metadata, dict):
    print("Error: metadata must be a JSON object")
    return 1

  try:
    event = create_event(
      event_type=args.event_type,
      skill=args.skill,
      repo=args.repo,
      metadata=metadata,
      timestamp=args.timestamp,
    )
  except ValidationError as e:
    print(f"Error: {e}")
    return 1

  outbox_dir = state_dir() / "outbox"
  append(event, outbox_dir)
  print(event.event_id)
  return 0
