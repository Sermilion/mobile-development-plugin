from __future__ import annotations

import argparse
import sys

import skill_bill
from skill_bill.config import state_dir, repo_root
from skill_bill.telemetry import capture, flush


def main() -> None:
  parser = argparse.ArgumentParser(prog="skill-bill", description="Skill Bill CLI runtime")
  subparsers = parser.add_subparsers(dest="command")

  telemetry_parser = subparsers.add_parser("telemetry", help="Telemetry commands")
  telemetry_sub = telemetry_parser.add_subparsers(dest="telemetry_command")
  capture.register(telemetry_sub)
  flush.register(telemetry_sub)

  subparsers.add_parser("version", help="Print version")
  subparsers.add_parser("doctor", help="Print runtime diagnostics")

  args = parser.parse_args()

  if args.command == "version":
    print(f"skill-bill {skill_bill.__version__}")
    sys.exit(0)

  if args.command == "doctor":
    sys.exit(run_doctor())

  if args.command == "telemetry":
    if hasattr(args, "func"):
      sys.exit(args.func(args))
    telemetry_parser.print_help()
    sys.exit(1)

  parser.print_help()
  sys.exit(1)


def run_doctor() -> int:
  sd = state_dir()
  outbox_file = sd / "outbox" / "events.jsonl"
  root = repo_root()

  print(f"skill-bill {skill_bill.__version__}")
  print(f"repo root:   {root or 'not found'}")
  print(f"state dir:   {sd}")
  print(f"outbox file: {outbox_file}")

  if outbox_file.exists():
    line_count = sum(1 for line in outbox_file.read_text(encoding="utf-8").splitlines() if line.strip())
    print(f"outbox size: {line_count} event(s)")
  else:
    print("outbox size: 0 event(s)")

  print("status: ok")
  return 0
