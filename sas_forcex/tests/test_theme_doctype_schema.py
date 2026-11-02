"""The ForceX Theme Settings DocType must match the engine's schema exactly.

theme_engine.SECTIONS is the single source of truth for every field, label and default.
The DocType JSON is generated from it (scripts/generate_theme_doctype.py). These tests
fail if someone edits one side and forgets the other — e.g. renames a field in the form
builder, or adds a setting to the engine without a field to store it.
No site needed.
"""

import json
import unittest
from pathlib import Path

from sas_forcex import theme_engine as te

DOCTYPE_DIR = Path(__file__).resolve().parents[1] / "sas_forcex" / "doctype"
SETTINGS = DOCTYPE_DIR / "forcex_theme_settings" / "forcex_theme_settings.json"
ROLE_ROW = DOCTYPE_DIR / "forcex_theme_role" / "forcex_theme_role.json"


def load(path):
	return json.loads(path.read_text(encoding="utf-8"))


class TestSettingsDocType(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.meta = load(SETTINGS)
		cls.fields = {f["fieldname"]: f for f in cls.meta["fields"]}

	def test_is_a_single_owned_by_this_module(self):
		self.assertEqual(self.meta["name"], te.DOCTYPE)
		self.assertEqual(self.meta["issingle"], 1)
		self.assertEqual(self.meta["module"], "SAS ForceX")

	def test_fields_are_exactly_the_generated_ones(self):
		self.assertEqual(self.meta["fields"], te.doctype_fields())

	def test_field_order_lists_every_field_once(self):
		self.assertEqual(self.meta["field_order"], [f["fieldname"] for f in self.meta["fields"]])

	def test_every_default_is_prefilled_in_the_form(self):
		for name, value in te.DEFAULTS.items():
			if name == "hide_search_for_roles":
				continue  # table field: starts empty
			self.assertIn(name, self.fields, name)
			self.assertEqual(self.fields[name].get("default"), te.as_doctype_default(value), name)

	def test_colour_settings_use_the_colour_picker(self):
		for name in te.COLOR_FIELDS:
			self.assertEqual(self.fields[name]["fieldtype"], "Color", name)

	def test_login_title_is_capped_at_30(self):
		self.assertEqual(self.fields["login_title"]["length"], 30)

	def test_only_system_manager_can_change_the_theme(self):
		self.assertEqual([p["role"] for p in self.meta["permissions"]], ["System Manager"])

	def test_export_import_buttons_are_on_the_form(self):
		"""Users could not find Export / Import inside the Actions menu: they also live
		on the form as Button fields, and buttons hold no value (not in DEFAULTS)."""
		for name in ("export_settings_btn", "import_settings_btn"):
			self.assertEqual(self.fields[name]["fieldtype"], "Button", name)
			self.assertNotIn(name, te.DEFAULTS)

	def test_role_table_points_at_the_child_doctype(self):
		f = self.fields["hide_search_for_roles"]
		self.assertEqual((f["fieldtype"], f["options"]), ("Table MultiSelect", "ForceX Theme Role"))


class TestRoleRowDocType(unittest.TestCase):
	def test_child_table_has_one_role_link(self):
		meta = load(ROLE_ROW)
		self.assertEqual(meta["istable"], 1)
		self.assertEqual(
			[(f["fieldname"], f["fieldtype"], f["options"]) for f in meta["fields"]],
			[("role", "Link", "Role")],
		)


if __name__ == "__main__":
	unittest.main()
