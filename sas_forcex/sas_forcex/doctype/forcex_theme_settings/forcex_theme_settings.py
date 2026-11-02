# Copyright (c) 2026, SAS Infosystem Pvt Ltd and contributors
# For license information, please see license.txt

"""ForceX Theme Settings — controller.

The rules live in sas_forcex/theme_engine.py and are shared with Import, so the form
and an imported file can never disagree about what is valid:

  1. every setting goes through engine.validate_value (hex colours, 0/1 checks,
     select options, text lengths, no '<' in custom CSS, safe image URLs) and is
     stored in its cleaned form (#abc → #AABBCC); all problems are reported at once;
  2. engine.cross_field_errors checks rules between settings (Image background
     needs an image);
  3. low-contrast colour pairs give a warning, never an error — it is the owner's
     brand, we only point out what may be hard to read.
After saving, the Desk boot cache and the website page cache are cleared so the
change shows on the next page load.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import escape_html

from sas_forcex import theme_engine as engine
from sas_forcex.theme import clear_caches


class ForceXThemeSettings(Document):
	def validate(self):
		self._apply_rulebook()
		self._check_cross_field_rules()
		self._warn_low_contrast()

	def on_update(self):
		clear_caches()

	# ------------------------------------------------------------------ rules
	def _apply_rulebook(self):
		problems = []
		for name in engine.DEFAULTS:
			if name == "hide_search_for_roles":
				continue  # Link rows: Frappe already checks each role exists
			value = self.get(name)
			if value in (None, ""):
				continue  # empty means "use the ForceX default"
			try:
				self.set(name, engine.validate_value(name, value))
			except ValueError as err:
				problems.append(f"{engine.label_of(name)}: {err}")
		_throw_all(problems, _("Please fix these settings"))

	def _check_cross_field_rules(self):
		_throw_all(engine.cross_field_errors(self.as_dict()), _("Please fix these settings"))

	def _warn_low_contrast(self):
		warnings = engine.contrast_warnings(self.as_dict())
		if warnings:
			frappe.msgprint(
				"<br>".join(escape_html(w) for w in warnings),
				title=_("Readability check"),
				indicator="orange",
			)


def _throw_all(messages, title):
	"""One error dialog listing every problem, instead of fixing them one save at a time."""
	if messages:
		frappe.throw("<br>".join(escape_html(m) for m in messages), title=title)
