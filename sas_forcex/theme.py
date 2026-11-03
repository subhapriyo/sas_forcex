"""ForceX theme — Frappe glue.

All decisions (schema, defaults, rules, colours, CSS, login options, import checks)
live in sas_forcex/forcex_theme/ — reached through sas_forcex.theme_engine — which has
no Frappe import and is unit-tested on its own. This module only:

  * reads "ForceX Theme Settings" (falling back to defaults if it is missing),
  * hands the result to the Desk (extend_bootinfo) and website pages
    (update_website_context),
  * applies the ForceX branding to the Desk boot: ForceX ERP logo instead of ERPNext's,
    About / Support rows hidden from the Help menu (rules in forcex_theme/branding.py),
  * decides who sees the ForceX Theme icon on the apps screen (can_open_theme_settings),
  * sets System Settings → App Name to "ForceX" (apply_app_name: install + patch),
  * serves the settings page buttons: Clear Cache, Reset, Export, Import (preview + apply),
  * prefills the settings on install / migrate.

Errors in the theme are logged and swallowed: a broken setting must never stop
someone from logging in or loading the Desk.
"""

import frappe
from frappe import _

from sas_forcex import theme_engine as engine

DOCTYPE = engine.DOCTYPE
_log = frappe.logger("sas_forcex.theme")


# ------------------------------------------------------------------ reading settings
def get_settings() -> dict:
	"""Saved values as a plain dict ({} if the DocType is not synced on this site yet)."""
	try:
		return frappe.get_cached_doc(DOCTYPE).as_dict()
	except Exception:
		return {}


def get_client_config(for_login=False, roles=None) -> dict:
	try:
		return engine.build_config(get_settings(), for_login=for_login, roles=roles or ())
	except Exception:
		_log.exception("ForceX theme config failed; falling back to stock look")
		return {"enabled": 0, "classes": [], "css": ""}


# ------------------------------------------------------------------ hooks.py
def extend_bootinfo(bootinfo):
	"""hooks.py → extend_bootinfo. Runs after Frappe has built desk_settings, app_data and
	navbar_settings, so all three can be adjusted here."""
	roles = [] if frappe.session.user == "Administrator" else frappe.get_roles()
	config = get_client_config(roles=roles)
	bootinfo.forcex_theme = config

	# "Hide search for these roles": switch off the search the v16 sidebar builds
	# (Sidebar.add_standard_items checks desk_settings.search_bar).
	if config.get("hide_search") and bootinfo.get("desk_settings") is not None:
		bootinfo.desk_settings["search_bar"] = 0

	_brand_boot(bootinfo, config)


def _brand_boot(bootinfo, config):
	"""ForceX logos and menus. Logged and skipped on error, like the theme itself."""
	try:
		# Logos are the brand, not the theme: swapped even when the theme is switched off.
		# The browser gets the map too, for app data the Desk re-fetches after boot.
		bootinfo.forcex_brand = {"app_logos": engine.APP_LOGOS}
		if bootinfo.get("app_data"):
			bootinfo.app_data = engine.brand_app_data(bootinfo.app_data)

		# About / Support: hide the rows in the boot copy of Navbar Settings only.
		navbar = bootinfo.get("navbar_settings")
		if navbar and (config.get("hide_about") or config.get("hide_support")):
			navbar = navbar.as_dict() if hasattr(navbar, "as_dict") else frappe._dict(navbar)
			navbar.help_dropdown = [
				frappe._dict(row)
				for row in engine.hide_help_items(
					navbar.get("help_dropdown"), config.get("hide_about"), config.get("hide_support")
				)
			]
			bootinfo.navbar_settings = navbar
	except Exception:
		_log.exception("ForceX branding could not be applied to the boot")


def can_open_theme_settings() -> bool:
	"""hooks.py → add_to_apps_screen.has_permission: the ForceX Theme icon is shown to the
	people who may change the theme (the DocType is System Manager only)."""
	return "System Manager" in frappe.get_roles()


def update_website_context(context):
	"""hooks.py → update_website_context. Website pages get the theme; /login also gets its options.

	The snippet goes into head_html, not head_include: Frappe's login.html replaces the
	head_include block with its own stylesheet, while templates/includes/head.html prints
	head_html on every page. We append, so Website Settings → Head HTML is kept.
	"""
	path = (context.get("path") or "").strip("/")
	snippet = engine.render_head_script(get_client_config(for_login=(path == "login")))
	if snippet:
		return {"head_html": (context.get("head_html") or "") + snippet}


def after_install():
	"""hooks.py → after_install: prefill a fresh site with the ForceX defaults and name."""
	prefill_settings()
	apply_app_name()


def apply_app_name():
	"""System Settings → App Name: "ERPNext" / "Frappe" becomes "ForceX".

	It is the name in browser tab titles and in server-rendered text (emails), which the
	browser-side rebrand never sees. A name the site chose itself is kept. Written with
	set_single_value so no other System Settings validation or side effect runs."""
	current = frappe.db.get_single_value("System Settings", "app_name")
	new = engine.rebranded_app_name(current)
	if new != current:
		frappe.db.set_single_value("System Settings", "app_name", new)
		clear_caches()


# ------------------------------------------------------------------ settings page buttons
def clear_caches():
	"""Desk reads the theme from the cached boot payload, website pages from cached HTML."""
	from frappe.website.utils import clear_cache as clear_website_cache

	frappe.clear_cache()
	clear_website_cache()


@frappe.whitelist(methods=["POST"])
def clear_theme_cache():
	"""'Clear Cache' button on ForceX Theme Settings."""
	frappe.only_for("System Manager")
	clear_caches()
	return _("Cache cleared. Reload any open tabs to see the latest theme.")


@frappe.whitelist(methods=["POST"])
def reset_theme_settings():
	"""'Reset to ForceX defaults' button: every field back to the prefilled palette."""
	frappe.only_for("System Manager")
	prefill_settings(overwrite=True)
	return _("Theme reset to the ForceX defaults.")


# ------------------------------------------------------------------ prefill
def prefill_settings(overwrite=False):
	"""Fill empty fields with the defaults (or every field when overwrite=True).

	Only empty values are touched by default, so re-running on migrate never
	undoes choices a System Manager has already made.
	"""
	doc = frappe.get_single(DOCTYPE)
	changed = False
	for name, value in engine.DEFAULTS.items():
		if name == "hide_search_for_roles":
			if overwrite and doc.get(name):
				doc.set(name, [])
				changed = True
			continue
		if overwrite or doc.get(name) in (None, ""):
			doc.set(name, value)
			changed = True
	if changed:
		doc.flags.ignore_permissions = True
		doc.save()
	return doc


# ------------------------------------------------------------------ export / import
# Import is two steps: preview_theme_import (dry run, shown to the user) then
# import_theme_settings (validates again — a preview is never trusted — and saves).
@frappe.whitelist()
def export_theme_settings():
	"""'Export' button: the whole theme as a JSON-ready dict (the form downloads it)."""
	frappe.only_for("System Manager")
	return engine.export_payload(
		get_settings(), exported_on=frappe.utils.now(), site=getattr(frappe.local, "site", None)
	)


def _validate_import(data):
	"""Engine dry run, with this site's roles and uploaded files looked up one by one."""
	return engine.validate_import(
		data,
		get_settings(),
		existing_roles=lambda role: bool(frappe.db.exists("Role", role)),
		existing_files=lambda url: bool(frappe.db.exists("File", {"file_url": url})),
	)


@frappe.whitelist(methods=["POST"])
def preview_theme_import(data):
	"""Step 1: what an import would change, skip and warn about. Saves nothing."""
	frappe.only_for("System Manager")
	report = _validate_import(data)
	report.pop("values")  # the browser only needs the summary
	return report


@frappe.whitelist(methods=["POST"])
def import_theme_settings(data):
	"""Step 2: apply the file. Blocking errors abort before anything is written; the save
	then runs the normal ForceX Theme Settings validation as well."""
	frappe.only_for("System Manager")
	report = _validate_import(data)
	if not report["ok"]:
		frappe.throw(
			"<br>".join(frappe.utils.escape_html(e) for e in report["errors"]), title=_("Cannot import theme")
		)

	doc = frappe.get_single(DOCTYPE)
	for name, value in report["values"].items():
		if name == "hide_search_for_roles":
			doc.set(name, [{"role": r} for r in value])  # table rows
		else:
			doc.set(name, value)
	doc.save()
	return {"applied": len(report["changes"]), "unchanged": report["unchanged"], "skipped": report["skipped"]}
