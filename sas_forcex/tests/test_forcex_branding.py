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


# ------------------------------------------------------------------------- app name
class TestAppName(unittest.TestCase):
	"""System Settings → App Name: shown in tab titles and server-rendered text (emails)."""

	def test_upstream_names_become_forcex(self):
		for upstream in ("ERPNext", "Frappe", "", None):
			self.assertEqual(br.rebranded_app_name(upstream), "ForceX", repr(upstream))

	def test_a_name_the_site_chose_is_kept(self):
		for own in ("ForceX", "Sufalam ERP", "erpnext-custom"):
			self.assertEqual(br.rebranded_app_name(own), own)


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

	def test_website_splash_and_favicon_use_the_forcex_erp_mark(self):
		# ERPNext sets both to its own logo through the same hook; the last app wins.
		self.assertEqual(self.hooks.website_context["splash_image"], br.FORCEX_ERP_LOGO)
		self.assertEqual(self.hooks.website_context["favicon"], br.FORCEX_ERP_LOGO)


if __name__ == "__main__":
	unittest.main()
