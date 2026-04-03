#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import json
import os
import re
import sqlite3
import sys


DEFAULT_DB_PATH = Path.home() / ".skill-bill" / "review-metrics.db"
DB_ENVIRONMENT_KEY = "SKILL_BILL_REVIEW_DB"
EVENT_TYPES = ("accepted", "dismissed", "fix_requested")

REVIEW_RUN_ID_PATTERN = re.compile(r"^Review run ID:\s*(?P<value>[A-Za-z0-9._:-]+)\s*$", re.MULTILINE)
SUMMARY_PATTERNS = {
  "routed_skill": re.compile(r"^Routed to:\s*(?P<value>.+?)\s*$", re.MULTILINE),
  "detected_scope": re.compile(r"^Detected review scope:\s*(?P<value>.+?)\s*$", re.MULTILINE),
  "detected_stack": re.compile(r"^Detected stack:\s*(?P<value>.+?)\s*$", re.MULTILINE),
  "execution_mode": re.compile(r"^Execution mode:\s*(?P<value>inline|delegated)\s*$", re.MULTILINE),
}
FINDING_PATTERN = re.compile(
  r"^\s*-\s+\[(?P<finding_id>F-\d{3})\]\s+"
  r"(?P<severity>Blocker|Major|Minor)\s+\|\s+"
  r"(?P<confidence>High|Medium|Low)\s+\|\s+"
  r"(?P<location>[^|]+?)\s+\|\s+"
  r"(?P<description>.+)$",
  re.MULTILINE,
)


@dataclass(frozen=True)
class ImportedFinding:
  finding_id: str
  severity: str
  confidence: str
  location: str
  description: str
  finding_text: str


@dataclass(frozen=True)
class ImportedReview:
  review_run_id: str
  raw_text: str
  routed_skill: str | None
  detected_scope: str | None
  detected_stack: str | None
  execution_mode: str | None
  findings: tuple[ImportedFinding, ...]


def resolve_db_path(cli_value: str | None) -> Path:
  candidate = cli_value or os.environ.get(DB_ENVIRONMENT_KEY)
  if candidate:
    return Path(candidate).expanduser().resolve()
  return DEFAULT_DB_PATH.expanduser().resolve()


def ensure_database(path: Path) -> sqlite3.Connection:
  path.parent.mkdir(parents=True, exist_ok=True)
  connection = sqlite3.connect(path)
  connection.execute("PRAGMA foreign_keys = ON")
  connection.row_factory = sqlite3.Row
  connection.executescript(
    """
    CREATE TABLE IF NOT EXISTS review_runs (
      review_run_id TEXT PRIMARY KEY,
      routed_skill TEXT,
      detected_scope TEXT,
      detected_stack TEXT,
      execution_mode TEXT,
      source_path TEXT,
      raw_text TEXT NOT NULL,
      imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS findings (
      review_run_id TEXT NOT NULL,
      finding_id TEXT NOT NULL,
      severity TEXT NOT NULL,
      confidence TEXT NOT NULL,
      location TEXT NOT NULL,
      description TEXT NOT NULL,
      finding_text TEXT NOT NULL,
      PRIMARY KEY (review_run_id, finding_id),
      FOREIGN KEY (review_run_id) REFERENCES review_runs(review_run_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS feedback_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      review_run_id TEXT NOT NULL,
      finding_id TEXT NOT NULL,
      event_type TEXT NOT NULL CHECK (event_type IN ('accepted', 'dismissed', 'fix_requested')),
      note TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (review_run_id, finding_id) REFERENCES findings(review_run_id, finding_id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_feedback_events_run
      ON feedback_events(review_run_id, finding_id, event_type);
    """
  )
  return connection


def parse_review(text: str) -> ImportedReview:
  review_run_match = REVIEW_RUN_ID_PATTERN.search(text)
  if not review_run_match:
    raise ValueError("Review output is missing 'Review run ID: <review-run-id>'.")

  findings: list[ImportedFinding] = []
  seen_ids: set[str] = set()
  for match in FINDING_PATTERN.finditer(text):
    finding_id = match.group("finding_id")
    if finding_id in seen_ids:
      raise ValueError(f"Review output contains duplicate finding id '{finding_id}'.")
    seen_ids.add(finding_id)
    findings.append(
      ImportedFinding(
        finding_id=finding_id,
        severity=match.group("severity"),
        confidence=match.group("confidence"),
        location=match.group("location").strip(),
        description=match.group("description").strip(),
        finding_text=match.group(0).strip(),
      )
    )

  if not findings:
    raise ValueError(
      "Review output is missing machine-readable findings. Expected lines like "
      "'- [F-001] Major | High | file:line | description'."
    )

  return ImportedReview(
    review_run_id=review_run_match.group("value"),
    raw_text=text,
    routed_skill=extract_summary_value(text, "routed_skill"),
    detected_scope=extract_summary_value(text, "detected_scope"),
    detected_stack=extract_summary_value(text, "detected_stack"),
    execution_mode=extract_summary_value(text, "execution_mode"),
    findings=tuple(findings),
  )


def extract_summary_value(text: str, key: str) -> str | None:
  match = SUMMARY_PATTERNS[key].search(text)
  if not match:
    return None
  return match.group("value").strip()


def read_input(input_path: str) -> tuple[str, str | None]:
  if input_path == "-":
    return (sys.stdin.read(), None)
  path = Path(input_path).expanduser().resolve()
  return (path.read_text(encoding="utf-8"), str(path))


def save_imported_review(
  connection: sqlite3.Connection,
  review: ImportedReview,
  *,
  source_path: str | None,
) -> None:
  with connection:
    connection.execute(
      """
      INSERT INTO review_runs (
        review_run_id,
        routed_skill,
        detected_scope,
        detected_stack,
        execution_mode,
        source_path,
        raw_text
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(review_run_id) DO UPDATE SET
        routed_skill = excluded.routed_skill,
        detected_scope = excluded.detected_scope,
        detected_stack = excluded.detected_stack,
        execution_mode = excluded.execution_mode,
        source_path = excluded.source_path,
        raw_text = excluded.raw_text
      """,
      (
        review.review_run_id,
        review.routed_skill,
        review.detected_scope,
        review.detected_stack,
        review.execution_mode,
        source_path,
        review.raw_text,
      ),
    )

    for finding in review.findings:
      connection.execute(
        """
        INSERT INTO findings (
          review_run_id,
          finding_id,
          severity,
          confidence,
          location,
          description,
          finding_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(review_run_id, finding_id) DO UPDATE SET
          severity = excluded.severity,
          confidence = excluded.confidence,
          location = excluded.location,
          description = excluded.description,
          finding_text = excluded.finding_text
        """,
        (
          review.review_run_id,
          finding.finding_id,
          finding.severity,
          finding.confidence,
          finding.location,
          finding.description,
          finding.finding_text,
        ),
      )


def record_feedback(
  connection: sqlite3.Connection,
  *,
  review_run_id: str,
  finding_ids: list[str],
  event_type: str,
  note: str,
) -> None:
  if not review_exists(connection, review_run_id):
    raise ValueError(f"Unknown review run id '{review_run_id}'. Import the review first.")

  missing_findings = [
    finding_id
    for finding_id in finding_ids
    if not finding_exists(connection, review_run_id, finding_id)
  ]
  if missing_findings:
    raise ValueError(
      "Unknown finding ids for review run "
      f"'{review_run_id}': {', '.join(sorted(missing_findings))}"
    )

  with connection:
    for finding_id in finding_ids:
      connection.execute(
        """
        INSERT INTO feedback_events (review_run_id, finding_id, event_type, note)
        VALUES (?, ?, ?, ?)
        """,
        (review_run_id, finding_id, event_type, note),
      )


def review_exists(connection: sqlite3.Connection, review_run_id: str) -> bool:
  row = connection.execute(
    "SELECT 1 FROM review_runs WHERE review_run_id = ?",
    (review_run_id,),
  ).fetchone()
  return row is not None


def finding_exists(connection: sqlite3.Connection, review_run_id: str, finding_id: str) -> bool:
  row = connection.execute(
    """
    SELECT 1
    FROM findings
    WHERE review_run_id = ? AND finding_id = ?
    """,
    (review_run_id, finding_id),
  ).fetchone()
  return row is not None


def stats_payload(connection: sqlite3.Connection, review_run_id: str | None) -> dict[str, object]:
  filters = ""
  parameters: tuple[str, ...] = ()
  if review_run_id:
    filters = "WHERE review_run_id = ?"
    parameters = (review_run_id,)
    if not review_exists(connection, review_run_id):
      raise ValueError(f"Unknown review run id '{review_run_id}'.")

  total_findings = scalar(
    connection,
    f"SELECT COUNT(*) FROM findings {filters}",
    parameters,
  )
  accepted_findings = scalar(
    connection,
    f"""
    SELECT COUNT(DISTINCT review_run_id || ':' || finding_id)
    FROM feedback_events
    {filters if filters else ''}
    AND event_type = 'accepted'
    """ if filters else """
    SELECT COUNT(DISTINCT review_run_id || ':' || finding_id)
    FROM feedback_events
    WHERE event_type = 'accepted'
    """,
    parameters,
  )
  dismissed_findings = scalar(
    connection,
    f"""
    SELECT COUNT(DISTINCT review_run_id || ':' || finding_id)
    FROM feedback_events
    {filters if filters else ''}
    AND event_type = 'dismissed'
    """ if filters else """
    SELECT COUNT(DISTINCT review_run_id || ':' || finding_id)
    FROM feedback_events
    WHERE event_type = 'dismissed'
    """,
    parameters,
  )
  fix_requested_findings = scalar(
    connection,
    f"""
    SELECT COUNT(DISTINCT review_run_id || ':' || finding_id)
    FROM feedback_events
    {filters if filters else ''}
    AND event_type = 'fix_requested'
    """ if filters else """
    SELECT COUNT(DISTINCT review_run_id || ':' || finding_id)
    FROM feedback_events
    WHERE event_type = 'fix_requested'
    """,
    parameters,
  )
  actionable_findings = scalar(
    connection,
    f"""
    SELECT COUNT(DISTINCT review_run_id || ':' || finding_id)
    FROM feedback_events
    {filters if filters else ''}
    AND event_type IN ('accepted', 'fix_requested')
    """ if filters else """
    SELECT COUNT(DISTINCT review_run_id || ':' || finding_id)
    FROM feedback_events
    WHERE event_type IN ('accepted', 'fix_requested')
    """,
    parameters,
  )

  acceptance_rate = 0.0
  if total_findings:
    acceptance_rate = round(actionable_findings / total_findings, 3)

  payload: dict[str, object] = {
    "review_run_id": review_run_id,
    "total_findings": total_findings,
    "accepted_findings": accepted_findings,
    "dismissed_findings": dismissed_findings,
    "fix_requested_findings": fix_requested_findings,
    "actionable_findings": actionable_findings,
    "acceptance_rate": acceptance_rate,
  }
  return payload


def scalar(connection: sqlite3.Connection, query: str, parameters: tuple[str, ...]) -> int:
  row = connection.execute(query, parameters).fetchone()
  if row is None:
    return 0
  return int(row[0])


def emit(payload: dict[str, object], output_format: str) -> None:
  if output_format == "json":
    print(json.dumps(payload, indent=2, sort_keys=True))
    return

  for key, value in payload.items():
    if value is None:
      continue
    print(f"{key}: {value}")


def import_review_command(args: argparse.Namespace) -> int:
  text, source_path = read_input(args.input)
  review = parse_review(text)
  connection = ensure_database(resolve_db_path(args.db))
  try:
    save_imported_review(connection, review, source_path=source_path)
  finally:
    connection.close()

  emit(
    {
      "db_path": str(resolve_db_path(args.db)),
      "review_run_id": review.review_run_id,
      "finding_count": len(review.findings),
      "routed_skill": review.routed_skill,
      "detected_scope": review.detected_scope,
      "detected_stack": review.detected_stack,
      "execution_mode": review.execution_mode,
    },
    args.format,
  )
  return 0


def record_feedback_command(args: argparse.Namespace) -> int:
  connection = ensure_database(resolve_db_path(args.db))
  try:
    record_feedback(
      connection,
      review_run_id=args.run_id,
      finding_ids=args.finding,
      event_type=args.event,
      note=args.note,
    )
  finally:
    connection.close()

  emit(
    {
      "db_path": str(resolve_db_path(args.db)),
      "review_run_id": args.run_id,
      "event_type": args.event,
      "recorded_findings": len(args.finding),
    },
    args.format,
  )
  return 0


def stats_command(args: argparse.Namespace) -> int:
  connection = ensure_database(resolve_db_path(args.db))
  try:
    payload = stats_payload(connection, args.run_id)
  finally:
    connection.close()

  payload["db_path"] = str(resolve_db_path(args.db))
  emit(payload, args.format)
  return 0


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description="Import Skill Bill review output and record explicit local review feedback metrics."
  )
  parser.add_argument(
    "--db",
    help=f"Optional SQLite path. Defaults to ${DB_ENVIRONMENT_KEY} or {DEFAULT_DB_PATH}.",
  )
  subparsers = parser.add_subparsers(dest="command", required=True)

  import_parser = subparsers.add_parser(
    "import-review",
    help="Import a review output file or stdin into the local SQLite store.",
  )
  import_parser.add_argument("input", nargs="?", default="-", help="Path to review text, or '-' for stdin.")
  import_parser.add_argument("--format", choices=("text", "json"), default="text")
  import_parser.set_defaults(handler=import_review_command)

  feedback_parser = subparsers.add_parser(
    "record-feedback",
    help="Record explicit feedback events for one or more findings in an imported review run.",
  )
  feedback_parser.add_argument("--run-id", required=True, help="Imported review run id.")
  feedback_parser.add_argument(
    "--event",
    choices=EVENT_TYPES,
    required=True,
    help="Feedback event type to record.",
  )
  feedback_parser.add_argument(
    "--finding",
    action="append",
    required=True,
    help="Finding id to update. Repeat the flag to record multiple findings.",
  )
  feedback_parser.add_argument("--note", default="", help="Optional note for the recorded feedback event.")
  feedback_parser.add_argument("--format", choices=("text", "json"), default="text")
  feedback_parser.set_defaults(handler=record_feedback_command)

  stats_parser = subparsers.add_parser(
    "stats",
    help="Show aggregate or per-run review acceptance metrics from the local SQLite store.",
  )
  stats_parser.add_argument("--run-id", help="Optional review run id to scope stats to one review.")
  stats_parser.add_argument("--format", choices=("text", "json"), default="text")
  stats_parser.set_defaults(handler=stats_command)
  return parser


def main(argv: list[str] | None = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv)

  try:
    return int(args.handler(args))
  except ValueError as error:
    print(str(error), file=sys.stderr)
    return 1


if __name__ == "__main__":
  raise SystemExit(main())
