"""ForceX theme — Frappe glue.

All decisions (schema, defaults, rules, colours, CSS, login options, import checks)
live in sas_forcex/forcex_theme/ — reached through sas_forcex.theme_engine — which has
no Frappe import and is unit-tested on its own. This module only:

  * reads "ForceX Theme Settings" (falling back to defaults if it is missing),
  * hands the result to the Desk (extend_bootinfo) and website pages
    (update_website_context),
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
	"""hooks.py → extend_bootinfo. Runs after Frappe has built desk_settings."""
	roles = [] if frappe.session.user == "Administrator" else frappe.get_roles()
	config = get_client_config(roles=roles)
	bootinfo.forcex_theme = config

	# "Hide search for these roles": switch off the search the v16 sidebar builds
	# (Sidebar.add_standard_items checks desk_settings.search_bar).
	if config.get("hide_search") and bootinfo.get("desk_settings") is not None:
		bootinfo.desk_settings["search_bar"] = 0


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
	"""hooks.py → after_install: prefill a fresh site with the ForceX defaults."""
	prefill_settings()


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
