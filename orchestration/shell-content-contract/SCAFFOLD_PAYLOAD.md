---
name: scaffold-payload
description: Payload schema for the new-skill scaffolder (SKILL-15). Documents the JSON contract consumed by `skill-bill new-skill --payload`, the `new_skill_scaffold` MCP tool, and the bill-new-skill-all-agents skill.
---

# Scaffold Payload Contract

This is the canonical payload schema for the new-skill scaffolder. Every
caller of `skill_bill.scaffold.scaffold(payload)` — the CLI, the MCP tool,
and the `bill-new-skill-all-agents` skill — ships a payload that conforms to
this schema. Mismatches raise specific named exceptions and abort the run;
no silent coercion.

## Versioning

- Required key: `scaffold_payload_version`.
- Current value: `"1.0"`.
- Any payload that declares a different version raises
  `ScaffoldPayloadVersionMismatchError`. Bump the scaffolder and every caller
  in lockstep when the contract changes.
- Version follows `MAJOR.MINOR`. Minor changes are additive; major changes
  are breaking.

## Required Keys

Every payload MUST include:

- `scaffold_payload_version` — exact match for the scaffolder's expected
  version string.
- `kind` — one of:
  - `"horizontal"` — placed under `skills/base/<name>/SKILL.md`.
  - `"platform-override-piloted"` — placed under
    `platform-packs/<slug>/<family>/<name>/SKILL.md` plus a manifest edit
    for shelled families. Pre-shell families are placed under
    `skills/<platform>/<name>/SKILL.md` with an interim-location note.
  - `"code-review-area"` — placed under
    `platform-packs/<slug>/code-review/<name>/SKILL.md` plus additions to
    `declared_code_review_areas` and `declared_files.areas` in the owning
    `platform.yaml`.
  - `"add-on"` — placed at `platform-packs/<slug>/addons/<name>.md` (flat;
    no sub-directory) and registered under the pack manifest's
    `declared_addons` list. Requires an existing pack with
    `governs_addons: true`.
- `name` — the canonical `bill-...` slug for the new skill.

## Conditionally Required Keys

- `platform` — required for `platform-override-piloted`, `code-review-area`,
  and `add-on`. Must be a recognized platform slug (e.g. `kotlin`, `kmp`,
  `backend-kotlin`, `php`, `go`, `agent-config`).
- `family` — required for `platform-override-piloted`. One of the known
  families:
  - Shelled: `code-review`, `quality-check`.
  - Pre-shell (see :data:`skill_bill.constants.PRE_SHELL_FAMILIES`):
    `feature-implement`, `feature-verify`.
- `area` — required for `code-review-area`. Must be one of the approved
  areas in :data:`skill_bill.shell_content_contract.APPROVED_CODE_REVIEW_AREAS`:
  `architecture`, `performance`, `platform-correctness`, `security`,
  `testing`, `api-contracts`, `persistence`, `reliability`, `ui`,
  `ux-accessibility`.

## Optional Keys

- `description` — one-line description copied into the frontmatter.
- `repo_root` — absolute path override used by tests. Defaults to the
  current working directory.

## Worked Examples

### Horizontal skill

```json
{
  "scaffold_payload_version": "1.0",
  "kind": "horizontal",
  "name": "bill-new-horizontal",
  "description": "Use for ..."
}
```

### Platform-override (piloted, code-review family)

```json
{
  "scaffold_payload_version": "1.0",
  "kind": "platform-override-piloted",
  "name": "bill-kotlin-code-review-new",
  "platform": "kotlin",
  "family": "code-review",
  "description": "..."
}
```

### Platform-override (piloted, quality-check family)

```json
{
  "scaffold_payload_version": "1.0",
  "kind": "platform-override-piloted",
  "name": "bill-php-quality-check",
  "platform": "php",
  "family": "quality-check"
}
```

This lands the skill at
`platform-packs/php/quality-check/bill-php-quality-check/SKILL.md` and edits
the owning pack's `platform.yaml` to register
`declared_quality_check_file: quality-check/bill-php-quality-check/SKILL.md`.
The scaffolded skill links the sibling sidecars `stack-routing.md` and
`telemetry-contract.md` just like the shelled code-review example above.

### Code-review area

```json
{
  "scaffold_payload_version": "1.0",
  "kind": "code-review-area",
  "name": "bill-kotlin-code-review-api-contracts",
  "platform": "kotlin",
  "area": "api-contracts"
}
```

### Add-on

```json
{
  "scaffold_payload_version": "1.0",
  "kind": "add-on",
  "name": "android-paging",
  "platform": "kmp"
}
```

This lands the add-on file at
`platform-packs/kmp/addons/android-paging.md` and appends a **single-file
placeholder entry** to `declared_addons` in
`platform-packs/kmp/platform.yaml` where both `implementation` and `review`
point at the same `addons/android-paging.md` file. The scaffolder uses
this default so a one-shot `new-skill` call always produces a contract-valid
manifest; callers who want the conventional
`<name>-implementation.md`/`<name>-review.md` split must either (1) pass a
richer `addon_entry` in the payload (see below) or (2) rename the
placeholder file and edit the manifest after scaffolding.

The pack must already declare `governs_addons: true`; the scaffolder refuses
to flip the flag on your behalf.

#### Richer entry override

To register separate implementation, review, and topic files in one
scaffold call, pass an `addon_entry` mapping. The scaffolder validates the
shape but does NOT create the additional files on your behalf — you are
expected to author them in the same commit:

```json
{
  "scaffold_payload_version": "1.0",
  "kind": "add-on",
  "name": "android-paging",
  "platform": "kmp",
  "addon_entry": {
    "slug": "android-paging",
    "implementation": "addons/android-paging-implementation.md",
    "review": "addons/android-paging-review.md",
    "topic_files": [
      "addons/android-paging-cursor-apis.md"
    ]
  }
}
```

`addon_entry` must be a mapping with a non-empty `slug`, `implementation`,
and `review`; a malformed shape raises `InvalidScaffoldPayloadError`.

## Loud-Fail Exception Catalog

All exceptions derive from `skill_bill.scaffold_exceptions.ScaffoldError`:

- `ScaffoldPayloadVersionMismatchError` — `scaffold_payload_version`
  disagrees with the scaffolder.
- `InvalidScaffoldPayloadError` — missing required key, malformed value, or
  unapproved area slug.
- `UnknownSkillKindError` — `kind` is not one of the four supported kinds.
- `UnknownPreShellFamilyError` — pre-shell family not in
  `PRE_SHELL_FAMILIES`.
- `MissingPlatformPackError` — platform pack (`platform-packs/<slug>/`)
  does not exist; create a conforming `platform.yaml` before retrying.
- `MissingSupportingFileTargetError` — a file name declared in
  `RUNTIME_SUPPORTING_FILES` for this skill is not registered in
  `SUPPORTING_FILE_TARGETS`; register the target or drop the reference.
  The scaffolder never silently skips supporting-file symlinks.
- `SkillAlreadyExistsError` — target path already occupied.
- `ScaffoldValidatorError` — post-scaffold validator run failed; all
  staged changes are rolled back.
- `ScaffoldRollbackError` — rollback itself failed (the only failure mode
  that may leave the repo partially mutated).
