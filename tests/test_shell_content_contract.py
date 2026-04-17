"""Fixture-based accept/reject coverage for the shell+content contract loader.

Mirrors the fixture pattern used by ``test_validate_agent_configs_e2e.py`` so
acceptance and rejection paths are first-class. Every rejection asserts the
specific named exception and that the offending artifact is referenced in the
error message.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skill_bill import shell_content_contract  # noqa: E402
from skill_bill.shell_content_contract import (  # noqa: E402
  AddonDeclaration,
  ContractVersionMismatchError,
  InvalidManifestSchemaError,
  MissingContentFileError,
  MissingManifestError,
  MissingRequiredSectionError,
  OrphanAddonFileError,
  PlatformPack,
  PyYAMLMissingError,
  SHELL_CONTRACT_VERSION,
  load_addon_content,
  load_platform_pack,
  load_quality_check_content,
  scan_orphan_addon_files,
)


FIXTURES_ROOT = ROOT / "tests" / "fixtures" / "shell_content_contract"


class ShellContentContractLoaderTest(unittest.TestCase):
  maxDiff = None

  def test_loads_valid_pack(self) -> None:
    pack = load_platform_pack(FIXTURES_ROOT / "valid_pack")
    self.assertIsInstance(pack, PlatformPack)
    self.assertEqual(pack.slug, "valid_pack")
    self.assertEqual(pack.contract_version, SHELL_CONTRACT_VERSION)
    self.assertEqual(pack.declared_code_review_areas, ("architecture",))
    self.assertEqual(pack.routing_signals.strong, (".fixture",))
    self.assertEqual(pack.routed_skill_name, "bill-valid_pack-code-review")

  def test_rejects_missing_manifest(self) -> None:
    with self.assertRaises(MissingManifestError) as context:
      load_platform_pack(FIXTURES_ROOT / "missing_manifest")
    self.assertIn("missing_manifest", str(context.exception))
    self.assertIn("platform.yaml", str(context.exception))

  def test_rejects_missing_content_file(self) -> None:
    with self.assertRaises(MissingContentFileError) as context:
      load_platform_pack(FIXTURES_ROOT / "missing_content_file")
    message = str(context.exception)
    self.assertIn("missing_content_file", message)
    self.assertIn("baseline", message)
    self.assertIn("code-review/SKILL.md", message)

  def test_rejects_bad_version(self) -> None:
    with self.assertRaises(ContractVersionMismatchError) as context:
      load_platform_pack(FIXTURES_ROOT / "bad_version")
    message = str(context.exception)
    self.assertIn("bad_version", message)
    self.assertIn("9.99", message)
    self.assertIn(SHELL_CONTRACT_VERSION, message)

  def test_rejects_missing_section(self) -> None:
    with self.assertRaises(MissingRequiredSectionError) as context:
      load_platform_pack(FIXTURES_ROOT / "missing_section")
    message = str(context.exception)
    self.assertIn("missing_section", message)
    self.assertIn("## Telemetry Ceremony Hooks", message)

  def test_rejects_invalid_schema(self) -> None:
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_platform_pack(FIXTURES_ROOT / "invalid_schema")
    message = str(context.exception)
    self.assertIn("invalid_schema", message)
    self.assertIn("routing_signals", message)

  # --- Additional InvalidManifestSchemaError coverage (T-005) ------------

  def test_rejects_declared_code_review_areas_not_a_list(self) -> None:
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_platform_pack(FIXTURES_ROOT / "schema_areas_wrong_type")
    message = str(context.exception)
    self.assertIn("schema_areas_wrong_type", message)
    self.assertIn("declared_code_review_areas", message)

  def test_rejects_unapproved_area_in_declared_code_review_areas(self) -> None:
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_platform_pack(FIXTURES_ROOT / "schema_unapproved_area")
    message = str(context.exception)
    self.assertIn("schema_unapproved_area", message)
    self.assertIn("laravel", message)
    self.assertIn("declared area", message)

  def test_rejects_non_boolean_governs_addons(self) -> None:
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_platform_pack(FIXTURES_ROOT / "schema_governs_addons_wrong_type")
    message = str(context.exception)
    self.assertIn("schema_governs_addons_wrong_type", message)
    self.assertIn("governs_addons", message)

  # --- Additional contract-error coverage (A-003, P-001) -----------------

  def test_rejects_extra_area_in_declared_files(self) -> None:
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_platform_pack(FIXTURES_ROOT / "extra_area")
    message = str(context.exception)
    self.assertIn("extra_area", message)
    self.assertIn("declared_files.areas", message)
    self.assertIn("performance", message)

  def test_rejects_required_section_only_inside_fenced_code_block(self) -> None:
    with self.assertRaises(MissingRequiredSectionError) as context:
      load_platform_pack(FIXTURES_ROOT / "heading_in_fence")
    message = str(context.exception)
    self.assertIn("heading_in_fence", message)
    self.assertIn("## Specialist Scope", message)

  # --- PyYAML missing coverage (P-002) -----------------------------------

  def test_raises_pyyaml_missing_error_when_yaml_import_fails(self) -> None:
    with mock.patch.object(
      shell_content_contract,
      "_import_yaml",
      side_effect=PyYAMLMissingError(
        "PyYAML is required to load platform packs. Install it via the "
        "project venv (`./.venv/bin/pip install pyyaml>=6`) or run the "
        "validator through `.venv/bin/python3 scripts/validate_agent_configs.py`."
      ),
    ):
      with self.assertRaises(PyYAMLMissingError) as context:
        load_platform_pack(FIXTURES_ROOT / "valid_pack")
    message = str(context.exception)
    self.assertIn("PyYAML", message)
    self.assertIn(".venv/bin/pip install pyyaml", message)


class QualityCheckContentContractTest(unittest.TestCase):
  """SKILL-16: optional declared_quality_check_file loader coverage."""

  maxDiff = None

  def test_loads_quality_check_only_fixture(self) -> None:
    pack = load_platform_pack(FIXTURES_ROOT / "quality_check_only")
    self.assertIsNotNone(pack.declared_quality_check_file)
    resolved = load_quality_check_content(pack)
    self.assertEqual(resolved, pack.declared_quality_check_file)
    self.assertTrue(resolved.is_file())

  def test_loads_code_review_and_quality_check_fixture(self) -> None:
    pack = load_platform_pack(FIXTURES_ROOT / "code_review_and_quality_check")
    self.assertIsNotNone(pack.declared_quality_check_file)
    resolved = load_quality_check_content(pack)
    self.assertTrue(resolved.is_file())
    # Both code-review baseline and quality-check files must succeed.
    self.assertEqual(pack.declared_code_review_areas, ("architecture",))

  def test_rejects_quality_check_missing_file(self) -> None:
    pack = load_platform_pack(FIXTURES_ROOT / "quality_check_missing_file")
    with self.assertRaises(MissingContentFileError) as context:
      load_quality_check_content(pack)
    message = str(context.exception)
    self.assertIn("quality_check_missing_file", message)
    self.assertIn("does-not-exist.md", message)

  def test_rejects_quality_check_missing_section(self) -> None:
    pack = load_platform_pack(FIXTURES_ROOT / "quality_check_missing_section")
    with self.assertRaises(MissingRequiredSectionError) as context:
      load_quality_check_content(pack)
    message = str(context.exception)
    self.assertIn("quality_check_missing_section", message)
    self.assertIn("## Fix Strategy", message)

  def test_valid_pack_without_quality_check_key_is_none(self) -> None:
    """A pack that does NOT declare the key has declared_quality_check_file=None.

    Calling load_quality_check_content on such a pack raises
    MissingContentFileError rather than silently returning nothing.
    """
    pack = load_platform_pack(FIXTURES_ROOT / "valid_pack")
    self.assertIsNone(pack.declared_quality_check_file)
    with self.assertRaises(MissingContentFileError) as context:
      load_quality_check_content(pack)
    self.assertIn("valid_pack", str(context.exception))


class AddonContentContractTest(unittest.TestCase):
  """SKILL-17: declared_addons + load_addon_content + orphan scan coverage."""

  maxDiff = None

  def test_loads_valid_addons_pack(self) -> None:
    pack = load_platform_pack(FIXTURES_ROOT / "addons_valid")
    self.assertTrue(pack.governs_addons)
    self.assertEqual(len(pack.declared_addons), 1)
    declaration = pack.declared_addons[0]
    self.assertIsInstance(declaration, AddonDeclaration)
    self.assertEqual(declaration.slug, "fixture-addon")
    self.assertTrue(declaration.implementation.is_file())
    self.assertTrue(declaration.review.is_file())
    self.assertEqual(len(declaration.topic_files), 1)

    loaded = load_addon_content(pack, "fixture-addon")
    self.assertEqual(loaded, declaration)
    # No orphan files → orphan scan is a no-op.
    scan_orphan_addon_files(pack)

  def test_rejects_addons_missing_file(self) -> None:
    pack = load_platform_pack(FIXTURES_ROOT / "addons_missing_file")
    with self.assertRaises(MissingContentFileError) as context:
      load_addon_content(pack, "missing-file-addon")
    message = str(context.exception)
    self.assertIn("addons_missing_file", message)
    self.assertIn("missing-file-addon-review.md", message)

  def test_rejects_addons_governs_true_empty(self) -> None:
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_platform_pack(FIXTURES_ROOT / "addons_governs_true_empty")
    message = str(context.exception)
    self.assertIn("addons_governs_true_empty", message)
    self.assertIn("governs_addons", message)
    self.assertIn("declared_addons", message)

  def test_rejects_addons_governs_false_with_declared(self) -> None:
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_platform_pack(FIXTURES_ROOT / "addons_governs_false_declared")
    message = str(context.exception)
    self.assertIn("addons_governs_false_declared", message)
    self.assertIn("declared_addons", message)
    self.assertIn("governs_addons", message)

  def test_rejects_addons_slug_only(self) -> None:
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_platform_pack(FIXTURES_ROOT / "addons_slug_only")
    message = str(context.exception)
    self.assertIn("addons_slug_only", message)
    self.assertIn("implementation", message)

  def test_rejects_addons_duplicate_slug(self) -> None:
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_platform_pack(FIXTURES_ROOT / "addons_duplicate_slug")
    message = str(context.exception)
    self.assertIn("addons_duplicate_slug", message)
    self.assertIn("duplicate", message)
    self.assertIn("dup-addon", message)

  def test_rejects_addons_orphan_file(self) -> None:
    pack = load_platform_pack(FIXTURES_ROOT / "addons_orphan_file")
    with self.assertRaises(OrphanAddonFileError) as context:
      scan_orphan_addon_files(pack)
    message = str(context.exception)
    self.assertIn("addons_orphan_file", message)
    self.assertIn("orphan-wanderer.md", message)

  def test_load_addon_content_rejects_unknown_slug(self) -> None:
    pack = load_platform_pack(FIXTURES_ROOT / "addons_valid")
    with self.assertRaises(InvalidManifestSchemaError) as context:
      load_addon_content(pack, "does-not-exist")
    self.assertIn("does-not-exist", str(context.exception))

  def test_valid_pack_declared_quality_check_still_works(self) -> None:
    """Regression: the declared_quality_check_file flow stays unaffected.

    This guards against any accidental coupling between the add-on loader
    and the quality-check loader — both optional contract extensions must
    remain independently usable.
    """
    pack = load_platform_pack(FIXTURES_ROOT / "quality_check_only")
    self.assertIsNotNone(pack.declared_quality_check_file)
    resolved = load_quality_check_content(pack)
    self.assertTrue(resolved.is_file())
    # quality_check_only fixture does not govern add-ons and does not
    # declare any.
    self.assertFalse(pack.governs_addons)
    self.assertEqual(pack.declared_addons, ())


if __name__ == "__main__":
  unittest.main()
