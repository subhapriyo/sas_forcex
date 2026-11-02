# Copyright (c) 2026, SAS Infosystem Pvt Ltd and contributors
# For license information, please see license.txt

"""Integration tests for ForceX Theme Settings — need a site:

    bench --site forcex.localhost run-tests --module \
        sas_forcex.sas_forcex.doctype.forcex_theme_settings.test_forcex_theme_settings

The pure logic (colours, CSS, login config) is covered by sas_forcex/tests/ without a
site; these tests cover what only Frappe can: validation on save, the cache/reset
endpoints, permissions and what lands in the Desk boot.
"""

import frappe
from frappe.tests import IntegrationTestCase

from sas_forcex import theme, theme_engine

DOCTYPE = theme_engine.DOCTYPE


class TestForceXThemeSettings(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.doc = theme.prefill_settings(overwrite=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		theme.prefill_settings(overwrite=True)

	# ---------------------------------------------------------------- prefill / reset
	def test_prefill_sets_every_default(self):
		doc = frappe.get_single(DOCTYPE)
		self.assertEqual(doc.primary_btn_bg, "#0F3870")
		self.assertEqual(doc.primary_btn_bg_dark, theme_engine.DEFAULTS["primary_btn_bg_dark"])
		self.assertEqual(doc.login_title, theme_engine.DEFAULTS["login_title"])

	def test_prefill_keeps_saved_choices(self):
		self.doc.navbar_bg = "#112233"
		self.doc.save()
		theme.prefill_settings()  # what migrate does
		self.assertEqual(frappe.get_single(DOCTYPE).navbar_bg, "#112233")

	def test_reset_restores_defaults(self):
		self.doc.navbar_bg = "#112233"
		self.doc.save()
		theme.reset_theme_settings()
		self.assertEqual(frappe.get_single(DOCTYPE).navbar_bg, theme_engine.DEFAULTS["navbar_bg"])

	# ---------------------------------------------------------------- validation
	def test_short_hex_is_normalised(self):
		self.doc.navbar_bg = "#abc"
		self.doc.save()
		self.assertEqual(self.doc.navbar_bg, "#AABBCC")

	def test_invalid_colour_is_rejected(self):
		self.doc.navbar_bg = "red;}"
		self.assertRaises(frappe.ValidationError, self.doc.save)

	def test_login_title_longer_than_30_is_rejected(self):
		self.doc.login_title = "x" * 31
		self.assertRaises(frappe.ValidationError, self.doc.save)

	def test_custom_css_cannot_close_the_style_tag(self):
		self.doc.custom_css = "</style><script>alert(1)</script>"
		self.assertRaises(frappe.ValidationError, self.doc.save)

	def test_all_problems_are_reported_in_one_go(self):
		self.doc.navbar_bg = "red;}"
		self.doc.login_title = "x" * 31
		with self.assertRaises(frappe.ValidationError) as ctx:
			self.doc.save()
		self.assertIn("Header background", str(ctx.exception))
		self.assertIn("Login page title", str(ctx.exception))

	def test_form_enforces_the_same_limits_as_import(self):
		# Singles have no DB column to cap Data length, so the rulebook does it
		self.doc.side_panel_headline = "x" * 141
		self.assertRaises(frappe.ValidationError, self.doc.save)

	def test_low_contrast_warns_but_saves(self):
		self.doc.primary_btn_text = self.doc.primary_btn_bg
		frappe.clear_messages()
		self.doc.save()
		self.assertTrue(frappe.get_message_log(), "a readability warning is shown")

	# ---------------------------------------------------------------- permissions
	def test_cache_and_reset_need_system_manager(self):
		frappe.set_user("Guest")
		self.assertRaises(frappe.PermissionError, theme.clear_theme_cache)
		self.assertRaises(frappe.PermissionError, theme.reset_theme_settings)

	def test_clear_cache_works_for_admin(self):
		self.assertTrue(theme.clear_theme_cache())

	# ---------------------------------------------------------------- boot / website
	def test_boot_carries_the_theme(self):
		boot = frappe._dict(desk_settings=frappe._dict(search_bar=1))
		theme.extend_bootinfo(boot)
		self.assertEqual(boot.forcex_theme["enabled"], 1)
		self.assertIn("--fxh-primary-btn-bg", boot.forcex_theme["css"])

	def test_search_hidden_for_a_listed_role(self):
		self.doc.set("hide_search_for_roles", [{"role": "System Manager"}])
		self.doc.save()
		user = frappe.db.get_value(
			"Has Role",
			{"role": "System Manager", "parent": ["!=", "Administrator"], "parenttype": "User"},
			"parent",
		)
		if not user:
			self.skipTest("needs a non-Administrator System Manager on this site")
		frappe.set_user(user)
		boot = frappe._dict(desk_settings=frappe._dict(search_bar=1))
		theme.extend_bootinfo(boot)
		self.assertEqual(boot.desk_settings.search_bar, 0)

	def test_administrator_always_keeps_search(self):
		self.doc.set("hide_search_for_roles", [{"role": "System Manager"}])
		self.doc.save()
		boot = frappe._dict(desk_settings=frappe._dict(search_bar=1))
		theme.extend_bootinfo(boot)
		self.assertEqual(boot.desk_settings.search_bar, 1)

	def test_disabled_theme_adds_nothing_to_the_login_page(self):
		self.doc.enabled = 0
		self.doc.save()
		self.assertIsNone(theme.update_website_context({"path": "login"}))

	def test_login_page_gets_title_and_head_snippet(self):
		self.doc.login_title = "Welcome to ForceX"
		self.doc.save()
		ctx = theme.update_website_context({"path": "login", "head_include": ""})
		self.assertIn("Welcome to ForceX", ctx["head_include"])
		self.assertIn('id="fxh-theme-vars"', ctx["head_include"])

	# ---------------------------------------------------------------- export / import
	def test_export_import_round_trip(self):
		self.doc.navbar_bg = "#112233"
		self.doc.save()
		exported = frappe.as_json(theme.export_theme_settings())
		theme.reset_theme_settings()
		result = theme.import_theme_settings(exported)
		self.assertEqual(result["skipped"], [])
		self.assertEqual(frappe.get_single(DOCTYPE).navbar_bg, "#112233")

	def test_import_skips_roles_missing_on_this_site(self):
		data = frappe.as_json(
			{
				"format": theme_engine.EXPORT_FORMAT,
				"version": 1,
				"settings": {"hide_search_for_roles": ["No Such Role 123"]},
			}
		)
		result = theme.import_theme_settings(data)
		self.assertTrue(any("No Such Role 123" in s for s in result["skipped"]))

	def test_import_rejects_a_foreign_file(self):
		self.assertRaises(frappe.ValidationError, theme.import_theme_settings, '{"hello": 1}')

	def test_export_and_import_need_system_manager(self):
		frappe.set_user("Guest")
		self.assertRaises(frappe.PermissionError, theme.export_theme_settings)
		self.assertRaises(frappe.PermissionError, theme.preview_theme_import, "{}")
		self.assertRaises(frappe.PermissionError, theme.import_theme_settings, "{}")

	def test_preview_lists_changes_and_saves_nothing(self):
		report = theme.preview_theme_import(_theme_file({"navbar_bg": "#112233"}))
		self.assertTrue(report["ok"])
		self.assertEqual([c["field"] for c in report["changes"]], ["navbar_bg"])
		self.assertNotIn("values", report)
		self.assertEqual(frappe.get_single(DOCTYPE).navbar_bg, theme_engine.DEFAULTS["navbar_bg"])

	def test_blocked_import_writes_nothing(self):
		# a background image that is not uploaded on this site → blocking error
		data = _theme_file(
			{
				"navbar_bg": "#112233",
				"login_background": "Image",
				"login_background_image": "/files/not-on-this-site-123.jpg",
			}
		)
		self.assertFalse(theme.preview_theme_import(data)["ok"])
		self.assertRaises(frappe.ValidationError, theme.import_theme_settings, data)
		self.assertEqual(frappe.get_single(DOCTYPE).navbar_bg, theme_engine.DEFAULTS["navbar_bg"])

	def test_empty_file_is_rejected(self):
		self.assertRaises(frappe.ValidationError, theme.import_theme_settings, "")


def _theme_file(settings):
	return frappe.as_json({"format": theme_engine.EXPORT_FORMAT, "version": 1, "settings": settings})
