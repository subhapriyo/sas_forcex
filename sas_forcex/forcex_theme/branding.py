"""ForceX branding: which upstream logos and menu rows are swapped or hidden.

Plain Python like the rest of this package: it decides, sas_forcex/theme.py applies it to
the Desk boot, and public/js/forcex_harbour.bundle.js repeats the logo swap in the browser
for app data the Desk fetches again after boot.

  * App logos — ERPNext ships its blue "E" mark through `add_to_apps_screen` and
    `app_logo_url`. Frappe copies that into `frappe.boot.app_data`, which feeds the
    apps screen, the app switcher and the dock rail, so swapping it there swaps it
    everywhere the Desk draws the app.
  * Brand settings — a few site settings put "Frappe" / "ERPNext" in front of people
    from the server side, where the browser-side rebrand (forcex_rebrand.bundle.js)
    cannot reach: tab titles, emails, authenticator apps, the OAuth consent screen and
    the website footer. BRAND_SETTINGS lists exactly those; each is changed only while
    it still holds an upstream default, so a value a site chose is never overwritten.
    Values that code compares ("Frappe Mail", the "Frappe" login provider, DocType
    names) are deliberately NOT in the list: rewriting them would break features.
  * Standalone app pages — HRMS serves /hr/... (Roster) and /hrms (mobile app) as
    self-contained Vite pages that load no Desk or website scripts, so nothing renamed
    "Frappe HR" there. sas_forcex.theme.after_request adds the rebrand script to the
    <head> of those pages as they leave the server; their own files are not touched.
  * Help menu — Frappe's standard Help rows "About" and "Frappe Support" (Navbar
    Settings). Rows are recognised by what they do, so a renamed or translated label
    still matches, and rows a site added itself are never touched.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ------------------------------------------------------------------------- icon files
# Served from sas_forcex/public/images (bench build links them under /assets/sas_forcex/).
FORCEX_ERP_LOGO = "/assets/sas_forcex/images/forcex-erp-logo.svg"
THEME_SETTINGS_ICON = "/assets/sas_forcex/images/forcex-theme-settings.svg"

# app_name → the ForceX logo shown for it. Sent to the browser as-is.
APP_LOGOS: dict[str, str] = {"erpnext": FORCEX_ERP_LOGO}

# Upstream image URLs that should never be shown (used for single URLs, e.g. splash).
_REPLACED_URLS: dict[str, str] = {
	"/assets/erpnext/images/erpnext-logo.svg": FORCEX_ERP_LOGO,
	"/assets/erpnext/images/erpnext-favicon.svg": FORCEX_ERP_LOGO,
}


def rebrand_url(url: str | None) -> str | None:
	"""An upstream ERPNext image URL → the ForceX one; anything else unchanged."""
	return _REPLACED_URLS.get(url, url) if url else url


def brand_app_data(app_data) -> list[dict]:
	"""A copy of `frappe.boot.app_data` with ForceX logos for the apps in APP_LOGOS.

	`app_logo_url` may be one URL or a [light, dark] pair; a pair is replaced as a pair so
	the Desk keeps finding a list where it expects one. The input is never modified.
	"""
	out = []
	for app in app_data or []:
		logo = APP_LOGOS.get(app.get("app_name"))
		if logo:
			current = app.get("app_logo_url")
			app = {**app, "app_logo_url": [logo] * len(current) if isinstance(current, list) else logo}
		out.append(app)
	return out


# ------------------------------------------------------------------------- brand settings
APP_NAME = "ForceX"


@dataclass(frozen=True)
class BrandSetting:
	"""One single-DocType field that carries the product name."""

	doctype: str
	field: str
	value: str  # what ForceX stores
	replaces: tuple  # upstream defaults; anything else was chosen by the site and is kept
	shown_in: str  # where people see it (for reviewers)


BRAND_SETTINGS: tuple[BrandSetting, ...] = (
	BrandSetting(
		"System Settings",
		"app_name",
		APP_NAME,
		("ERPNext", "Frappe", "", None),
		"browser tab titles; emails and the login page when the website has no name",
	),
	BrandSetting(
		"System Settings",
		"otp_issuer_name",
		APP_NAME,
		("Frappe Framework", "Frappe", "", None),
		"the account name in authenticator apps (two-factor login)",
	),
	# An empty website name falls back to System Settings → App Name, so empty is fine.
	BrandSetting(
		"Website Settings",
		"app_name",
		APP_NAME,
		("Frappe", "ERPNext"),
		"login page, website pages and email headers",
	),
	# Empty shows Frappe's "Built on Frappe" footer.
	BrandSetting(
		"Website Settings",
		"footer_powered",
		f"Powered by {APP_NAME}",
		("", None),
		"the website footer",
	),
	BrandSetting(
		"OAuth Settings",
		"resource_name",
		APP_NAME,
		("Frappe Framework Application", "", None),
		"the OAuth sign-in consent screen",
	),
)


def brand_setting_updates(current: dict) -> list[BrandSetting]:
	"""The settings to change, given {(doctype, field): stored value}.

	A (doctype, field) missing from `current` does not exist on this site and is skipped.
	"""
	return [
		s
		for s in BRAND_SETTINGS
		if (s.doctype, s.field) in current and current[(s.doctype, s.field)] in s.replaces
	]


# ------------------------------------------------------------------------- standalone app pages
# URL prefixes of upstream single-page apps that bring their own HTML: HRMS's Roster
# (website_route_rules: /hr/<path> → roster) and its mobile app (/hrms).
STANDALONE_APP_PREFIXES = ("/hr", "/hrms")
REBRAND_MARKER = "data-forcex-rebrand"  # on our <script> tag, so it is added only once
_HEAD_END = re.compile(r"</head\s*>", re.IGNORECASE)


def is_standalone_app_page(path: str | None) -> bool:
	"""/hr, /hr/roster/..., /hrms, /hrms/... — but not /hrx or /desk/hr."""
	path = path or ""
	return any(path == p or path.startswith(p + "/") for p in STANDALONE_APP_PREFIXES)


def inject_head(html: str, snippet: str) -> str:
	"""`snippet` placed just before </head> (once). HTML without a head is returned as is."""
	if not html or REBRAND_MARKER in html:
		return html
	match = _HEAD_END.search(html)
	if not match:
		return html
	return html[: match.start()] + snippet + html[match.start() :]


# ------------------------------------------------------------------------- Help menu
# Frappe's own rows (frappe/hooks.py → standard_help_items) and the desktop page's
# avatar menu (frappe/desk/page/desktop/desktop.js) use these labels.
ABOUT_LABEL = "About"
SUPPORT_LABEL = "Frappe Support"
_SUPPORT_SITES = ("frappe.io/support", "support.frappe.io")


def _is_about(row: dict) -> bool:
	return "show_about" in (row.get("action") or "") or row.get("item_label") == ABOUT_LABEL


def _is_support(row: dict) -> bool:
	route = row.get("route") or ""
	return any(site in route for site in _SUPPORT_SITES) or row.get("item_label") == SUPPORT_LABEL


def hide_help_items(rows, hide_about: bool, hide_support: bool) -> list[dict]:
	"""Copies of the Help menu rows, with About / Support marked hidden as requested.

	The Desk already skips rows with `hidden` set (SidebarHeader.get_help_siblings), so
	marking them is enough — and Navbar Settings itself is never edited.
	"""
	out = []
	for row in rows or []:
		row = dict(row)
		if (hide_about and _is_about(row)) or (hide_support and _is_support(row)):
			row["hidden"] = 1
		out.append(row)
	return out


def desktop_menu_labels_to_hide(hide_about: bool, hide_support: bool) -> list[str]:
	"""Rows to drop from the desktop page's avatar menu, which is built in the browser."""
	return [label for flag, label in ((hide_about, ABOUT_LABEL), (hide_support, SUPPORT_LABEL)) if flag]
