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
  * adds the rebrand script to HRMS's standalone pages, /hr and /hrms (after_request),
  * writes the ForceX name into the brand settings that server-rendered text reads —
    app name, authenticator issuer, OAuth resource, website footer (apply_brand_settings:
    install + patch),
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


def logos_on() -> bool:
	"""ForceX app logos on this site? 'Use ForceX app logos', or SAS Fortuna installed."""
	try:
		option = engine.coerce_settings(get_settings())["use_forcex_logos"]
		return engine.logos_enabled(option, frappe.get_installed_apps())
	except Exception:
		_log.exception("Could not tell whether ForceX app logos are on")
		return False


def _brand_boot(bootinfo, config):
	"""ForceX logos and menus. Logged and skipped on error, like the theme itself."""
	try:
		# Logos are the brand, not the theme: they follow their own option, not 'enabled'.
		# The browser gets the maps too (empty when logos are off), for app data the Desk
		# re-fetches after boot and for upstream logos drawn inside pages.
		logos = logos_on()
		bootinfo.forcex_brand = engine.brand_config(logos)
		if logos and bootinfo.get("app_data"):
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
	"""hooks.py → add_to_apps_screen.has_permission: who sees the ForceX Theme icon.

	Administrator always; other System Managers while Navigation → 'Show ForceX Theme
	icon' is on (rule: forcex_theme/branding.py → theme_icon_visible). Hiding the icon
	does not change permissions: System Managers can still open /desk/forcex-theme-settings.
	"""
	user = frappe.session.user
	show = engine.coerce_settings(get_settings())["show_theme_icon"]
	return engine.theme_icon_visible(user, frappe.get_roles(user), show)


def update_website_context(context):
	"""hooks.py → update_website_context. Website pages get the theme; /login also gets its options.

	The snippet goes into head_html, not head_include: Frappe's login.html replaces the
	head_include block with its own stylesheet, while templates/includes/head.html prints
	head_html on every page. We append, so Website Settings → Head HTML is kept.
	"""
	path = (context.get("path") or "").strip("/")
	updates = {}
	snippet = engine.render_head_script(get_client_config(for_login=(path == "login")))
	if snippet:
		updates["head_html"] = (context.get("head_html") or "") + snippet
	# The Desk splash and website favicon: ForceX ERP mark instead of ERPNext's, only where
	# ForceX app logos are on (the Desk page runs this hook too).
	if logos_on():
		updates.update(engine.brand_site_images(context))
	return updates or None


def after_request(response, request):
	"""hooks.py → after_request: put the ForceX rebrand script into the HTML of HRMS's
	standalone app pages (/hr/roster, /hrms), which load no Desk or website scripts and
	would otherwise still say "Frappe HR". Successful HTML pages only; never raises."""
	try:
		if not engine.is_standalone_app_page(getattr(request, "path", None)):
			return
		if response.status_code != 200 or response.mimetype != "text/html" or response.direct_passthrough:
			return
		from frappe.utils.jinja_globals import bundled_asset

		# These pages have no Desk boot, so the logo maps travel with the script.
		# "</" is escaped so the JSON can never close the <script> early.
		brand = frappe.as_json(engine.brand_config(logos_on()), indent=None).replace("</", "<\\/")
		src = frappe.utils.escape_html(bundled_asset("forcex_rebrand.bundle.js"))
		snippet = (
			f"<script {engine.REBRAND_MARKER}>window.forcex_brand = {brand};</script>"
			f'<script {engine.REBRAND_MARKER} src="{src}"></script>'
		)
		html = response.get_data(as_text=True)
		branded = engine.inject_head(html, snippet)
		if branded != html:
			response.set_data(branded)
	except Exception:
		_log.exception("ForceX rebrand script could not be added to %s", getattr(request, "path", "?"))


def after_install():
	"""hooks.py → after_install: prefill a fresh site with the ForceX defaults and name."""
	prefill_settings()
	apply_brand_settings()


# ------------------------------------------------------------------ new settings on old sites
def switch_on_new_checks(fields) -> list:
	"""For patches: store 1 for ForceX Theme Settings checks that default to on but have
	never been saved on this site. A DocType default only reaches a *new* Single, so on an
	existing site such a field would read 0. A value someone already saved is left alone.
	Returns the fields that were switched on."""
	switched = []
	for field in fields:
		stored = frappe.db.sql("select 1 from `tabSingles` where doctype=%s and field=%s", (DOCTYPE, field))
		if not stored:
			frappe.db.set_single_value(DOCTYPE, field, 1)
			switched.append(field)
	if switched:
		clear_caches()
	return switched


# ------------------------------------------------------------------ brand settings
def _stored_brand_settings() -> dict:
	"""{(doctype, field): stored value} for the BRAND_SETTINGS this site actually has."""
	current = {}
	for s in engine.BRAND_SETTINGS:
		if frappe.db.exists("DocType", s.doctype) and frappe.get_meta(s.doctype).has_field(s.field):
			current[(s.doctype, s.field)] = frappe.db.get_single_value(s.doctype, s.field)
	return current


def apply_brand_settings() -> list:
	"""Write "ForceX" into the settings that still hold an upstream name (rules and the
	reasons in forcex_theme/branding.py). Returns the settings that were changed.

	Written with set_single_value so no other settings validation or side effect runs.
	System Settings also keeps a copy of each value as a system default, which some code
	reads directly, so those copies are brought in step too — also when only they are stale.
	"""
	changed = engine.brand_setting_updates(_stored_brand_settings())
	for s in changed:
		frappe.db.set_single_value(s.doctype, s.field, s.value)

	defaults_synced = False
	for s in engine.BRAND_SETTINGS:
		if s.doctype == "System Settings":
			stored = frappe.db.get_single_value(s.doctype, s.field)
			if stored and frappe.db.get_default(s.field) != stored:
				frappe.db.set_default(s.field, stored)
				defaults_synced = True

	if changed or defaults_synced:
		clear_caches()
	return changed


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
