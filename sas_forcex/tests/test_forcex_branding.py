"""ForceX branding rules (sas_forcex/forcex_theme/branding.py) — no site needed.

Covers the three things the branding layer decides:
  * which app logos are swapped for ForceX ones (ERPNext → ForceX ERP),
  * which Help menu rows count as "About" and "Support",
  * that the icon files the hooks point at really exist and are valid SVG.
Written before branding.py (TDD).

Run: python -m unittest discover -s sas_forcex/tests -t .   (from apps/sas_forcex)
"""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from sas_forcex.forcex_theme import branding as br

PUBLIC = Path(__file__).resolve().parents[1] / "public"
ERPNEXT_LOGO = "/assets/erpnext/images/erpnext-logo.svg"


def asset_path(url: str) -> Path:
	"""/assets/sas_forcex/images/x.svg → <app>/sas_forcex/public/images/x.svg"""
	prefix = "/assets/sas_forcex/"
	assert url.startswith(prefix), url
	return PUBLIC / url[len(prefix) :]


def app(name, logo, **extra):
	return {"app_name": name, "app_title": name.title(), "app_logo_url": logo, **extra}


# ------------------------------------------------------------------------- app logos
class TestAppLogos(unittest.TestCase):
	def test_erpnext_gets_the_forcex_erp_logo(self):
		out = br.brand_app_data([app("erpnext", ERPNEXT_LOGO)])
		self.assertEqual(out[0]["app_logo_url"], br.FORCEX_ERP_LOGO)

	def test_other_apps_keep_their_own_logo(self):
		apps = [app("hrms", "/assets/hrms/images/frappe-hr-logo.svg"), app("frappe", "/f.svg")]
		self.assertEqual(br.brand_app_data(apps), apps)

	def test_a_light_and_dark_logo_pair_is_replaced_as_a_pair(self):
		out = br.brand_app_data([app("erpnext", [ERPNEXT_LOGO, "/assets/erpnext/images/dark.svg"])])
		self.assertEqual(out[0]["app_logo_url"], [br.FORCEX_ERP_LOGO, br.FORCEX_ERP_LOGO])

	def test_the_boot_payload_is_not_modified_in_place(self):
		apps = [app("erpnext", ERPNEXT_LOGO, dock=[{"module": "Selling"}])]
		out = br.brand_app_data(apps)
		self.assertEqual(apps[0]["app_logo_url"], ERPNEXT_LOGO)
		self.assertEqual(out[0]["dock"], [{"module": "Selling"}])  # everything else carried over

	def test_missing_or_odd_input_is_harmless(self):
		self.assertEqual(br.brand_app_data(None), [])
		self.assertEqual(br.brand_app_data([]), [])
		self.assertEqual(br.brand_app_data([{"app_name": "erpnext"}])[0]["app_logo_url"], br.FORCEX_ERP_LOGO)

	def test_known_erpnext_image_urls_map_to_forcex(self):
		self.assertEqual(br.rebrand_url(ERPNEXT_LOGO), br.FORCEX_ERP_LOGO)
		self.assertEqual(br.rebrand_url("/assets/erpnext/images/erpnext-favicon.svg"), br.FORCEX_ERP_LOGO)
		self.assertEqual(br.rebrand_url("/files/my-logo.png"), "/files/my-logo.png")
		self.assertIsNone(br.rebrand_url(None))

	def test_the_browser_gets_the_same_logo_map(self):
		self.assertEqual(br.APP_LOGOS, {"erpnext": br.FORCEX_ERP_LOGO})


# ------------------------------------------------------------------------- Help menu rows
HELP = [
	{"item_label": "About", "item_type": "Action", "action": "frappe.ui.toolbar.show_about()"},
	{"item_label": "System Health", "item_type": "Route", "route": "/desk/system-health-report"},
	{"item_label": "Frappe Support", "item_type": "Route", "route": "https://frappe.io/support"},
]


class TestHelpItems(unittest.TestCase):
	def hidden(self, rows):
		return [r["item_label"] for r in rows if r.get("hidden")]

	def test_about_and_support_are_hidden(self):
		out = br.hide_help_items(HELP, hide_about=True, hide_support=True)
		self.assertEqual(self.hidden(out), ["About", "Frappe Support"])

	def test_each_switch_works_on_its_own(self):
		self.assertEqual(
			self.hidden(br.hide_help_items(HELP, hide_about=True, hide_support=False)), ["About"]
		)
		self.assertEqual(
			self.hidden(br.hide_help_items(HELP, hide_about=False, hide_support=True)), ["Frappe Support"]
		)

	def test_nothing_changes_when_both_are_off(self):
		self.assertEqual(self.hidden(br.hide_help_items(HELP, hide_about=False, hide_support=False)), [])

	def test_rows_are_recognised_by_what_they_do_not_only_by_label(self):
		# a renamed or translated label still points at show_about / the support site
		rows = [
			{"item_label": "Über", "action": "frappe.ui.toolbar.show_about()"},
			{"item_label": "Get help", "route": "https://support.frappe.io/help"},
		]
		self.assertEqual(len(self.hidden(br.hide_help_items(rows, hide_about=True, hide_support=True))), 2)

	def test_rows_a_site_added_itself_are_left_alone(self):
		rows = [{"item_label": "Our helpdesk", "route": "https://help.example.com"}]
		self.assertEqual(self.hidden(br.hide_help_items(rows, hide_about=True, hide_support=True)), [])

	def test_input_rows_are_not_modified(self):
		rows = [dict(r) for r in HELP]
		br.hide_help_items(rows, hide_about=True, hide_support=True)
		self.assertFalse(any(r.get("hidden") for r in rows))

	def test_the_browser_gets_the_labels_to_drop_from_the_desktop_menu(self):
		self.assertEqual(
			br.desktop_menu_labels_to_hide(hide_about=True, hide_support=True), ["About", "Frappe Support"]
		)
		self.assertEqual(br.desktop_menu_labels_to_hide(hide_about=False, hide_support=False), [])


# ------------------------------------------------------------------------- brand settings
# Site settings that put "Frappe" / "ERPNext" in front of people from the server side
# (tab titles, emails, authenticator apps, OAuth consent, website footer).
SYS, WEB, OAUTH = "System Settings", "Website Settings", "OAuth Settings"


def updates(current):
	"""{(doctype, field): new value} for the given stored values."""
	return {(s.doctype, s.field): s.value for s in br.brand_setting_updates(current)}


class TestBrandSettings(unittest.TestCase):
	def test_upstream_defaults_become_forcex(self):
		current = {
			(SYS, "app_name"): "ERPNext",
			(SYS, "otp_issuer_name"): "Frappe Framework",
			(WEB, "app_name"): "Frappe",
			(WEB, "footer_powered"): "",
			(OAUTH, "resource_name"): "Frappe Framework Application",
		}
		self.assertEqual(
			updates(current),
			{
				(SYS, "app_name"): "ForceX",
				(SYS, "otp_issuer_name"): "ForceX",
				(WEB, "app_name"): "ForceX",
				(WEB, "footer_powered"): "Powered by ForceX",
				(OAUTH, "resource_name"): "ForceX",
			},
		)

	def test_values_a_site_chose_are_kept(self):
		# sil-dev: its own company name and a custom footer link
		current = {
			(WEB, "app_name"): "Sufalam Industries Limited",
			(WEB, "footer_powered"): '<a href="#">ForceX</a>',
			(SYS, "otp_issuer_name"): "Sufalam ERP",
			(SYS, "app_name"): "ForceX",
		}
		self.assertEqual(updates(current), {})

	def test_an_empty_website_name_is_left_to_fall_back_to_the_system_name(self):
		# Frappe uses System Settings → App Name when the website one is empty
		self.assertEqual(updates({(WEB, "app_name"): ""}), {})
		self.assertEqual(updates({(WEB, "app_name"): None}), {})

	def test_settings_missing_on_a_site_are_skipped(self):
		self.assertEqual(updates({}), {})

	def test_every_rule_says_where_people_see_it(self):
		for s in br.BRAND_SETTINGS:
			self.assertTrue(s.shown_in, f"{s.doctype}.{s.field}")
			self.assertNotIn(s.value, s.replaces, "a rule must never re-apply to its own result")

	def test_logic_values_are_never_rewritten(self):
		# "Frappe Mail" (Email Account service) and the "Frappe" social-login provider are
		# compared in code; only these named display settings are ever touched.
		touched = {(s.doctype, s.field) for s in br.BRAND_SETTINGS}
		self.assertTrue(
			touched
			<= {
				(SYS, "app_name"),
				(SYS, "otp_issuer_name"),
				(WEB, "app_name"),
				(WEB, "footer_powered"),
				(OAUTH, "resource_name"),
			}
		)


# ------------------------------------------------------------------------- standalone app pages
# HRMS serves /hr/... (Roster) and /hrms (mobile app) as self-contained Vite pages that load
# no ForceX script, so "Frappe HR" survived there. The rebrand script is added to their HTML.
class TestStandaloneAppPages(unittest.TestCase):
	def test_hr_pages_are_recognised(self):
		for path in ("/hr", "/hr/", "/hr/roster/", "/hr/roster/month", "/hrms", "/hrms/home"):
			self.assertTrue(br.is_standalone_app_page(path), path)

	def test_other_pages_are_not(self):
		for path in ("/desk/hr", "/hrx", "/home", "/login", "/app/hr-settings", "", None):
			self.assertFalse(br.is_standalone_app_page(path), path)

	def test_the_script_goes_just_before_head_closes(self):
		html = "<html><head><title>Roster</title></head><body></body></html>"
		out = br.inject_head(html, "<script data-forcex-rebrand></script>")
		self.assertIn("<title>Roster</title><script data-forcex-rebrand></script></head>", out)

	def test_injection_happens_once(self):
		once = br.inject_head("<head></head>", "<script data-forcex-rebrand></script>")
		self.assertEqual(br.inject_head(once, "<script data-forcex-rebrand></script>"), once)

	def test_html_without_a_head_is_left_alone(self):
		self.assertEqual(br.inject_head("<p>hi</p>", "<script></script>"), "<p>hi</p>")
		self.assertEqual(br.inject_head("", "<script></script>"), "")

	def test_head_tag_case_does_not_matter(self):
		self.assertIn("x</HEAD>", br.inject_head("<HEAD></HEAD>", "x"))


# ------------------------------------------------------------------------- icon files
class TestIconFiles(unittest.TestCase):
	def check_svg(self, url):
		path = asset_path(url)
		self.assertTrue(path.exists(), f"missing icon file {path}")
		root = ET.parse(path).getroot()  # raises if the SVG is not well-formed
		self.assertTrue(root.tag.endswith("svg"))
		self.assertEqual(root.get("viewBox"), "0 0 100 100", "same 100x100 grid as the other app logos")

	def test_forcex_erp_logo_exists_and_is_valid(self):
		self.check_svg(br.FORCEX_ERP_LOGO)

	def test_theme_settings_icon_exists_and_is_valid(self):
		self.check_svg(br.THEME_SETTINGS_ICON)

	def test_icons_carry_an_accessible_title(self):
		for url in (br.FORCEX_ERP_LOGO, br.THEME_SETTINGS_ICON):
			root = ET.parse(asset_path(url)).getroot()
			titles = [el.text for el in root.iter() if el.tag.endswith("title")]
			self.assertTrue(titles and titles[0].strip(), f"{url} needs a <title>")


# ------------------------------------------------------------------------- hooks.py wiring
class TestHooks(unittest.TestCase):
	"""hooks.py is plain Python, so its branding entries can be checked without a site."""

	@classmethod
	def setUpClass(cls):
		from sas_forcex import hooks

		cls.hooks = hooks

	def test_theme_settings_has_an_icon_on_the_desk_apps_screen(self):
		(entry,) = self.hooks.add_to_apps_screen
		self.assertEqual(entry["name"], "sas_forcex")
		self.assertEqual(entry["logo"], br.THEME_SETTINGS_ICON)
		self.assertEqual(entry["route"], "/desk/forcex-theme-settings")
		self.assertLess(entry["sequence_id"], 1000, "sits before Framework (1000)")

	def test_only_people_who_can_open_the_settings_see_the_icon(self):
		(entry,) = self.hooks.add_to_apps_screen
		self.assertEqual(entry["has_permission"], "sas_forcex.theme.can_open_theme_settings")

	def test_standalone_app_pages_get_the_rebrand_script(self):
		self.assertIn("sas_forcex.theme.after_request", self.hooks.after_request)

	def test_website_splash_and_favicon_use_the_forcex_erp_mark(self):
		# ERPNext sets both to its own logo through the same hook; the last app wins.
		self.assertEqual(self.hooks.website_context["splash_image"], br.FORCEX_ERP_LOGO)
		self.assertEqual(self.hooks.website_context["favicon"], br.FORCEX_ERP_LOGO)


if __name__ == "__main__":
	unittest.main()
