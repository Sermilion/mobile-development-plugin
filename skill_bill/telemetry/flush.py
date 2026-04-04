from __future__ import annotations

import argparse

from skill_bill.config import state_dir
from skill_bill.telemetry.outbox import read_all


def register(subparsers: argparse._SubParsersAction) -> None:
  parser = subparsers.add_parser("flush", help="Flush captured telemetry events")
  parser.add_argument("--dry-run", action="store_true", help="Print events without sending")
  parser.add_argument("--limit", type=int, default=0, help="Process only the first N events (0 = all)")
  parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
  outbox_dir = state_dir() / "outbox"
  events = read_all(outbox_dir)

  if not events:
    print("Outbox is empty.")
    return 0

  if args.limit > 0:
    events = events[:args.limit]

  if args.dry_run:
    for event in events:
      print(event.to_json())
    print(f"\n{len(events)} event(s) in outbox.")
    return 0

  print(f"Flush target not configured. {len(events)} event(s) in outbox.")
  return 0
