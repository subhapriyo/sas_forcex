"""System Settings → App Name: "ERPNext" → "ForceX" on sites that already exist.

ERPNext sets App Name to "ERPNext" when it is installed; it shows in browser tab titles
and in emails. New sites get "ForceX" from sas_forcex.theme.after_install; this patch
does the same once for existing sites. A name the site chose itself is kept.
"""

from sas_forcex.theme import apply_app_name


def execute():
	apply_app_name()
