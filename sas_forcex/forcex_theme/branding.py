"""ForceX branding: which upstream logos and menu rows are swapped or hidden.

Plain Python like the rest of this package: it decides, sas_forcex/theme.py applies it to
the Desk boot, and public/js/forcex_harbour.bundle.js repeats the logo swap in the browser
for app data the Desk fetches again after boot.

  * App logos — every upstream app ships its own mark through `add_to_apps_screen` and
    `app_logo_url` (ERPNext's blue "E", Frappe HR's green tile, ...). Frappe copies that
    into `frappe.boot.app_data`, which feeds the apps screen, the app switcher and the
    dock rail, so swapping it there swaps it everywhere the Desk draws the app. Pages
    that draw an upstream logo themselves get it swapped in the browser instead: an
    <img> by its URL (LOGO_URL_SWAPS), an inline <svg> by its look (INLINE_LOGOS).
    Only on sites that want them (logos_enabled): the 'Use ForceX app logos' option,
    or always where SAS Fortuna is installed. Elsewhere every upstream logo stays.
  * ForceX Theme icon — who sees the ForceX Theme tile on the apps screen
    (theme_icon_visible: Administrator always; System Managers while the option is on).
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
# All app logos share one design: a 100x100 rounded tile, a white glyph, a ForceX accent.
_IMAGES = "/assets/sas_forcex/images"
FORCEX_ERP_LOGO = f"{_IMAGES}/forcex-erp-logo.svg"
THEME_SETTINGS_ICON = f"{_IMAGES}/forcex-theme-settings.svg"

# app_name → the ForceX logo shown for it (sent to the browser as-is). Only the upstream
# apps that have a Desk icon on our sites (sil-dev, fleeto) are listed; any other app,
# and our own apps (FLEETO, SAS Fortuna, ...), keep the logo they ship. To add one, see
# the README (Branding).
APP_LOGOS: dict[str, str] = {
	"erpnext": FORCEX_ERP_LOGO,
	"hrms": f"{_IMAGES}/forcex-hr-logo.svg",
	"india_compliance": f"{_IMAGES}/forcex-india-compliance-logo.svg",
	"frappe": f"{_IMAGES}/forcex-framework-logo.svg",
	"helpdesk": f"{_IMAGES}/forcex-helpdesk-logo.svg",
}

# The image files each upstream app uses for its logo (from its hooks.py), so pages that
# show one as an <img> get the ForceX logo of the same app.
UPSTREAM_LOGOS: dict[str, tuple[str, ...]] = {
	"erpnext": ("/assets/erpnext/images/erpnext-logo.svg", "/assets/erpnext/images/erpnext-favicon.svg"),
	"hrms": ("/assets/hrms/images/frappe-hr-logo.svg",),
	"india_compliance": ("/assets/india_compliance/images/india-compliance.svg",),
	"frappe": ("/assets/frappe/images/frappe-framework-logo.svg",),
	"helpdesk": ("/assets/helpdesk/desk/favicon.svg",),
}

# upstream logo URL → ForceX logo URL (derived, so the two maps can never disagree)
LOGO_URL_SWAPS: dict[str, str] = {url: APP_LOGOS[app] for app, urls in UPSTREAM_LOGOS.items() for url in urls}

# Logos drawn as inline <svg> (no URL to swap). Each is recognised by a CSS selector for
# its look and painted over with the ForceX logo in the browser (forcex_rebrand.bundle.js).
INLINE_LOGOS: tuple[dict, ...] = (
	# HRMS's Vue pages (Roster at /hr, the mobile app at /hrms): FrappeHRLogo.vue, a
	# 117x117 mint (#A1EEC9) tile.
	{"selector": 'svg[viewBox="0 0 117 117"]:has(path[fill="#A1EEC9"])', "logo": APP_LOGOS["hrms"]},
)


def rebrand_url(url: str | None) -> str | None:
	"""An upstream app's logo URL → the ForceX one; anything else unchanged."""
	return LOGO_URL_SWAPS.get(url, url) if url else url


# Apps whose sites always get the ForceX logos, whatever the option says.
LOGO_APPS = ("sas_fortuna",)


def logos_enabled(option, installed_apps) -> bool:
	"""Should this site show ForceX app logos? Yes when 'Use ForceX app logos' is ticked,
	or when one of LOGO_APPS is installed (checked live, so installing it later counts)."""
	return bool(option) or any(app in (installed_apps or ()) for app in LOGO_APPS)


def brand_config(logos: bool) -> dict:
	"""What the browser needs to brand logos: frappe.boot.forcex_brand on the Desk,
	window.forcex_brand on standalone app pages (see sas_forcex.theme.after_request).
	With logos off the maps are empty, so the browser swaps nothing."""
	if not logos:
		return {"app_logos": {}, "logo_swaps": {}, "inline_logos": []}
	return {
		"app_logos": dict(APP_LOGOS),
		"logo_swaps": dict(LOGO_URL_SWAPS),
		"inline_logos": [dict(i) for i in INLINE_LOGOS],
	}


def brand_site_images(context) -> dict:
	"""ForceX versions of the Desk splash and website favicon, when they are still an
	upstream app's logo (ERPNext sets both through its website_context hook). A site's own
	images from Website Settings are kept. Returns only what changes."""
	out = {}
	for key in ("splash_image", "favicon"):
		value = context.get(key)
		if value and rebrand_url(value) != value:
			out[key] = rebrand_url(value)
	return out


# ------------------------------------------------------------------------- ForceX Theme icon
def theme_icon_visible(user: str, roles, show: bool) -> bool:
	"""Should this user see the ForceX Theme tile on the apps screen?

	Administrator always does, so the settings can never be lost from view. Other
	System Managers (the only role that may open the settings) see it while the
	'Show ForceX Theme icon' option is on. Everyone else never does.
	"""
	if user == "Administrator":
		return True
	return bool(show) and "System Manager" in (roles or ())


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
