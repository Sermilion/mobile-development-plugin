"""Manifest-edit helpers for the new-skill scaffolder (SKILL-15).

Appends new entries to ``platform.yaml`` while preserving key order and any
human-authored comments as best-effort. The scaffolder snapshots the original
bytes before calling in, so rollback is byte-identical on failure. This module
only needs to perform an additive edit — pack renames, deletions, and moves
are not supported here.

The append is conservative: we operate on the text form of the YAML so that
PyYAML's round-trip rewrite doesn't reshuffle keys or strip comments. PyYAML
by itself does not preserve comments, so a pure ``yaml.safe_dump`` round-trip
would drop every ``#`` line in existing packs.
"""

from __future__ import annotations

from pathlib import Path
import re


# Matches the top-level ``declared_code_review_areas:`` list. Capture groups:
# 1. the existing list body (zero or more lines beginning with a ``-``)
_AREAS_LIST_PATTERN = re.compile(
  r"^declared_code_review_areas:\s*\n((?:[ \t]+-[^\n]*\n)*)",
  re.MULTILINE,
)

# Matches the ``declared_files:`` block and then the nested ``areas:`` list
# body. The manifest canon (see ``platform-packs/kotlin/platform.yaml``) uses
# two-space indentation so we match that literal shape.
_AREAS_FILES_PATTERN = re.compile(
  r"^(declared_files:\n(?:(?:[ \t]+[^\n]*\n)*?))(  areas:\n)((?:    [^\n]+\n)*)",
  re.MULTILINE,
)


def append_code_review_area(
  *,
  manifest_path: Path,
  area: str,
  relative_content_path: str,
) -> None:
  """Append ``area`` to ``declared_code_review_areas`` and ``declared_files.areas``.

  Args:
    manifest_path: absolute path to ``platform.yaml``.
    area: approved code-review area slug (e.g. ``"performance"``).
    relative_content_path: path to the new SKILL.md, relative to the
      platform-pack root (e.g.
      ``"code-review/bill-kotlin-code-review-performance/SKILL.md"``).

  The edit is additive and idempotent: attempting to append an area that is
  already declared is a no-op. Callers that want strict-add semantics should
  rely on :class:`SkillAlreadyExistsError` raised upstream when the skill
  directory already exists.
  """
  original_text = manifest_path.read_text(encoding="utf-8")
  updated = original_text

  updated = _append_area_to_list(updated, area)
  updated = _append_area_to_declared_files(updated, area, relative_content_path)

  if updated != original_text:
    manifest_path.write_text(updated, encoding="utf-8")


def _append_area_to_list(text: str, area: str) -> str:
  match = _AREAS_LIST_PATTERN.search(text)
  if match is None:
    raise ValueError(
      "Manifest is missing required 'declared_code_review_areas:' block; refusing to edit."
    )
  existing_body = match.group(1)
  if re.search(rf"^[ \t]+-\s*{re.escape(area)}\s*$", existing_body, re.MULTILINE):
    return text
  indent = _detect_list_indent(existing_body) or "  "
  insertion = f"{indent}- {area}\n"
  start, end = match.span()
  return text[:start] + f"declared_code_review_areas:\n{existing_body}{insertion}" + text[end:]


def _append_area_to_declared_files(text: str, area: str, relative_path: str) -> str:
  match = _AREAS_FILES_PATTERN.search(text)
  if match is None:
    raise ValueError(
      "Manifest is missing 'declared_files.areas:' block; refusing to edit."
    )
  block_prefix = match.group(1)
  areas_header = match.group(2)
  existing_body = match.group(3)
  if re.search(rf"^    {re.escape(area)}:\s", existing_body, re.MULTILINE):
    return text
  insertion = f"    {area}: {relative_path}\n"
  start, end = match.span()
  return text[:start] + block_prefix + areas_header + existing_body + insertion + text[end:]


def _detect_list_indent(list_body: str) -> str:
  """Pick up the existing list indent so we append with the same prefix.

  The kotlin/backend-kotlin/kmp packs all use two-space indentation, but
  we still detect it dynamically so a fork that uses four-space indents
  doesn't get a mixed-indent manifest after the scaffolder edits it.
  """
  for line in list_body.splitlines():
    stripped = line.lstrip(" \t")
    if stripped.startswith("- "):
      return line[: len(line) - len(stripped)]
  return ""


# Matches an existing ``declared_quality_check_file:`` top-level key. We
# preserve whatever path the user already wrote (idempotent append).
_QUALITY_CHECK_KEY_PATTERN = re.compile(
  r"^declared_quality_check_file:\s*(.+)$",
  re.MULTILINE,
)

# Matches the end of the ``declared_files:`` block — the block header plus
# any nested indented lines. We append the new top-level key immediately
# after this block (with a blank-line separator) to mirror the manifest
# canon (see ``platform-packs/kotlin/platform.yaml``).
_DECLARED_FILES_BLOCK_PATTERN = re.compile(
  r"^(declared_files:\n(?:(?:[ \t]+[^\n]*\n)*))",
  re.MULTILINE,
)


def set_declared_quality_check_file(
  *,
  manifest_path: Path,
  relative_content_path: str,
) -> None:
  """Register ``declared_quality_check_file`` on a platform.yaml manifest.

  The edit is additive and idempotent: if the key already exists, its value
  is replaced with ``relative_content_path``. Otherwise the key is appended
  as a new top-level entry immediately after the ``declared_files:`` block
  with a blank-line separator, mirroring the manifest canon.
  """
  original_text = manifest_path.read_text(encoding="utf-8")
  match = _QUALITY_CHECK_KEY_PATTERN.search(original_text)
  if match is not None:
    updated = (
      original_text[: match.start()]
      + f"declared_quality_check_file: {relative_content_path}"
      + original_text[match.end():]
    )
  else:
    block_match = _DECLARED_FILES_BLOCK_PATTERN.search(original_text)
    if block_match is None:
      raise ValueError(
        "Manifest is missing 'declared_files:' block; refusing to edit "
        "(declared_quality_check_file must be appended as a sibling)."
      )
    insertion = f"\ndeclared_quality_check_file: {relative_content_path}\n"
    end = block_match.end()
    updated = original_text[:end] + insertion + original_text[end:]

  if updated != original_text:
    manifest_path.write_text(updated, encoding="utf-8")


# Matches the start-of-line ``declared_addons:`` top-level list header plus
# any nested indented body lines (dashes followed by key/value). We either
# append under the existing header or emit a fresh block under
# ``declared_files:``.
_DECLARED_ADDONS_BLOCK_PATTERN = re.compile(
  r"^(declared_addons:\s*\n)((?:(?:[ \t]+[^\n]*\n)|(?:\s*\n))*)",
  re.MULTILINE,
)


def append_declared_addon(
  *,
  manifest_path: Path,
  entry: dict,
) -> None:
  """Append a new ``declared_addons`` entry on a platform.yaml manifest.

  Mirrors :func:`set_declared_quality_check_file` (SKILL-16) but for the
  list-shaped ``declared_addons`` key introduced in SKILL-17. The edit is
  additive and idempotent — appending the same slug twice raises so the
  caller sees the duplicate rather than silently no-opping. When the
  ``declared_addons:`` header is absent, we append a fresh block at the
  end of the file.

  Args:
    manifest_path: absolute path to ``platform.yaml``.
    entry: mapping with required ``slug``, ``implementation``, ``review``;
      optional ``topic_files`` list of strings.

  Raises:
    ValueError: when ``entry`` is malformed, or when ``slug`` already
      appears under ``declared_addons``.
  """
  slug = entry.get("slug")
  implementation = entry.get("implementation")
  review = entry.get("review")
  topic_files = entry.get("topic_files") or []
  if not isinstance(slug, str) or not slug:
    raise ValueError("append_declared_addon requires a non-empty 'slug'.")
  if not isinstance(implementation, str) or not implementation:
    raise ValueError("append_declared_addon requires a non-empty 'implementation'.")
  if not isinstance(review, str) or not review:
    raise ValueError("append_declared_addon requires a non-empty 'review'.")
  if not isinstance(topic_files, list):
    raise ValueError("append_declared_addon expects 'topic_files' to be a list when provided.")

  original_text = manifest_path.read_text(encoding="utf-8")

  # Duplicate-slug guard: match ``- slug: <slug>`` under any indentation.
  dup_pattern = re.compile(
    rf"^[ \t]*-[ \t]+slug:[ \t]+{re.escape(slug)}\s*$",
    re.MULTILINE,
  )
  if dup_pattern.search(original_text):
    raise ValueError(
      f"Manifest already declares an add-on with slug '{slug}'; duplicates are not allowed."
    )

  new_entry_lines = [
    f"  - slug: {slug}",
    f"    implementation: {implementation}",
    f"    review: {review}",
  ]
  if topic_files:
    new_entry_lines.append("    topic_files:")
    for topic in topic_files:
      new_entry_lines.append(f"      - {topic}")
  new_entry_block = "\n".join(new_entry_lines) + "\n"

  match = _DECLARED_ADDONS_BLOCK_PATTERN.search(original_text)
  if match is not None:
    insertion_point = match.end()
    updated = original_text[:insertion_point] + new_entry_block + original_text[insertion_point:]
  else:
    # Append a fresh block. Ensure a trailing newline separates prior
    # content and our new block.
    prefix = original_text if original_text.endswith("\n") else original_text + "\n"
    updated = prefix + "\ndeclared_addons:\n" + new_entry_block

  if updated != original_text:
    manifest_path.write_text(updated, encoding="utf-8")


__all__ = [
  "append_code_review_area",
  "append_declared_addon",
  "set_declared_quality_check_file",
]
