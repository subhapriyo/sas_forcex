"""Replace "Frappe" / "ERPNext" with "ForceX" in the brand settings of existing sites.

Covers System Settings (app name, authenticator issuer), Website Settings (app name,
footer) and OAuth Settings (resource name) — see BRAND_SETTINGS in
sas_forcex/forcex_theme/branding.py. Only upstream default values are replaced; a value
the site chose itself is kept. New sites get the same from after_install. Idempotent.
"""

from sas_forcex.theme import apply_brand_settings


def execute():
	apply_brand_settings()
