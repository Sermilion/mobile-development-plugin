from __future__ import annotations

import dataclasses
import json
import re
import uuid
from datetime import datetime, timezone


EVENT_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
SKILL_NAME_PATTERN = re.compile(r"^bill-[a-z0-9-]+$")

MetadataValue = str | int | float | bool | None


@dataclasses.dataclass(frozen=True)
class TelemetryEvent:
  event_id: str
  event_type: str
  skill: str
  timestamp: str
  repo: str
  metadata: dict[str, MetadataValue]

  def to_json(self) -> str:
    return json.dumps(dataclasses.asdict(self), separators=(",", ":"))

  @classmethod
  def from_json(cls, raw: str) -> TelemetryEvent:
    data = json.loads(raw)
    fields = {f.name for f in dataclasses.fields(cls)}
    filtered = {k: v for k, v in data.items() if k in fields}
    return cls(**filtered)


class ValidationError(Exception):
  pass


def create_event(
  event_type: str,
  skill: str,
  repo: str = "",
  metadata: dict[str, MetadataValue] | None = None,
  timestamp: str | None = None,
  event_id: str | None = None,
) -> TelemetryEvent:
  if not event_type or not EVENT_TYPE_PATTERN.match(event_type):
    raise ValidationError(
      f"event_type must be lowercase alphanumeric with hyphens, got '{event_type}'"
    )

  if not skill or not SKILL_NAME_PATTERN.match(skill):
    raise ValidationError(
      f"skill must match bill-<name> pattern, got '{skill}'"
    )

  return TelemetryEvent(
    event_id=event_id or str(uuid.uuid4()),
    event_type=event_type,
    skill=skill,
    timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
    repo=repo,
    metadata=metadata or {},
  )
