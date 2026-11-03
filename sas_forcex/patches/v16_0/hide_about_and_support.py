"""Switch on "Hide About" and "Hide Support" on sites that already have ForceX Theme Settings.

The two checks default to 1, but a DocType default only reaches a *new* Single; on an
existing site the fields would read 0. So: where nobody has stored a value yet, store 1.
A value someone already saved (on or off) is left alone. Runs once per site on migrate.
"""

import frappe

from sas_forcex.theme import DOCTYPE, clear_caches

FIELDS = ("hide_about", "hide_support")


def _is_stored(field: str) -> bool:
	return bool(frappe.db.sql("select 1 from `tabSingles` where doctype=%s and field=%s", (DOCTYPE, field)))


def execute():
	changed = False
	for field in FIELDS:
		if not _is_stored(field):
			frappe.db.set_single_value(DOCTYPE, field, 1)
			changed = True
	if changed:
		clear_caches()
