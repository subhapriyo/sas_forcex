"""ForceX name in the brand settings on sites that already exist (first version: App Name).

Kept under its original name so sites that already ran it are not affected; it now
applies the full rule list, as rebrand_brand_settings does. Idempotent.
"""

from sas_forcex.theme import apply_brand_settings


def execute():
	apply_brand_settings()
