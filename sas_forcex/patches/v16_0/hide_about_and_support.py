"""Switch on "Hide About" and "Hide Support" on sites that already have ForceX Theme Settings.

Both default to on, but a DocType default only reaches a new Single, so existing sites
would read 0. Values someone already saved are kept (see theme.switch_on_new_checks).
"""

from sas_forcex.theme import switch_on_new_checks


def execute():
	switch_on_new_checks(("hide_about", "hide_support"))
