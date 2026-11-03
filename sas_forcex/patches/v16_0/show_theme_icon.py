"""Switch on "Show ForceX Theme icon on the apps screen" on sites that already exist.

It defaults to on (the icon was always shown before this option existed), but a DocType
default only reaches a new Single. A value someone already saved is kept.
"""

from sas_forcex.theme import switch_on_new_checks


def execute():
	switch_on_new_checks(("show_theme_icon",))
