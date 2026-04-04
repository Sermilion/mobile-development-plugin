from __future__ import annotations

import os
from pathlib import Path


def state_dir() -> Path:
  override = os.environ.get("SKILL_BILL_STATE_DIR")
  if override:
    path = Path(override)
  else:
    path = Path.home() / ".skill-bill"
  path.mkdir(parents=True, exist_ok=True)
  return path


def repo_root() -> Path | None:
  candidate = Path(__file__).resolve().parent.parent
  if (candidate / "skills").is_dir() and (candidate / "AGENTS.md").is_file():
    return candidate
  return None
