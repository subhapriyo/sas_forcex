"""Prefill ForceX Theme Settings after the settings page grew from ~15 to ~140 fields.

Runs once per site on `bench migrate` (post_model_sync, so the new fields exist):
  1. values still equal to the FIRST Harbour page's defaults were never chosen by
     anyone, so they are cleared and take the new ForceX (prototype) defaults;
  2. real choices from the first page are carried over
     (page_background → body_bg, login_box_position Center → Default);
  3. every still-empty field is filled with the ForceX defaults.
Anything a System Manager actually picked is kept.
"""

import frappe

from sas_forcex.theme import DOCTYPE, prefill_settings

# defaults of the first Harbour settings page (2026-11-02, morning)
OLD_DEFAULTS = {"primary_color": "#0D1B2A", "accent_color": "#FF8A00", "page_background": "#F4F6F9"}
# old fieldname → new fieldname (stored in tabSingles under the old name)
RENAMED = {"page_background": "body_bg"}


def _stored(field):
	row = frappe.db.sql("select value from `tabSingles` where doctype=%s and field=%s", (DOCTYPE, field))
	return row[0][0] if row else None


def execute():
	frappe.reload_doc("sas_forcex", "doctype", "forcex_theme_role")
	frappe.reload_doc("sas_forcex", "doctype", "forcex_theme_settings")

	# 1. untouched old defaults → empty, so step 3 fills the new palette
	for field, old_default in OLD_DEFAULTS.items():
		if (_stored(field) or "").upper() == old_default:
			frappe.db.sql("delete from `tabSingles` where doctype=%s and field=%s", (DOCTYPE, field))

	# 2. carry over real choices
	for old, new in RENAMED.items():
		value = _stored(old)
		if value and not _stored(new):
			frappe.db.set_single_value(DOCTYPE, new, value)
	if _stored("login_box_position") == "Center":
		frappe.db.set_single_value(DOCTYPE, "login_box_position", "Default")

	# 3. fill the rest
	frappe.clear_document_cache(DOCTYPE, DOCTYPE)
	prefill_settings()
