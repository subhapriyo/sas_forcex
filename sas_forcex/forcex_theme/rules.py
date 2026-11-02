"""Rules for setting values — one rulebook shared by the settings form and Import.

coerce_settings     any raw values → complete, typed, safe settings (used before CSS)
validate_value      accept/clean one value or say why not (form save + import)
cross_field_errors  rules between settings
contrast_warnings   readability check (never blocks)
"""

from __future__ import annotations

import re

from .colours import contrast, normalize_hex
from .schema import _LEGACY_SELECT, DEFAULTS, FIELDS, LOGIN_TITLE_MAX, label_of

MIN_CONTRAST = 4.5  # WCAG AA for normal-size text

# Only our own files or plain http(s) URLs, and no characters that could close url("...")
_SAFE_URL = re.compile(r"^(/files/|/assets/|https?://)[\w\-./:%?=&~+@,]+$")

# Text limits for values (Data fields use their own `length`)
TEXT_MAX = {"text": 1_000, "code": 20_000}


def _role_names(rows):
	names = []
	for row in rows or []:
		name = row.get("role") if isinstance(row, dict) else row
		name = (name or "").strip() if isinstance(name, str) else ""
		if name and name not in names:
			names.append(name)
	return names


def coerce_settings(raw: dict | None) -> dict:
	"""Return a complete, typed, safe settings dict.

	Unknown keys are dropped, empty values take the default, colours that are not
	valid hex fall back to the default (so nothing odd can reach a <style> tag),
	selects outside their options fall back, and the login title is capped.
	"""
	raw = raw or {}
	out = {}
	for name, default in DEFAULTS.items():
		base = name[:-5] if name.endswith("_dark") and name[:-5] in FIELDS else name
		f = FIELDS[base]
		value = raw.get(name)
		if f.kind == "color":
			out[name] = normalize_hex(value, default)
		elif f.kind == "check":
			try:
				out[name] = 1 if int(value if value not in (None, "") else default) else 0
			except (TypeError, ValueError):
				out[name] = int(default)
		elif f.kind == "select":
			value = _LEGACY_SELECT.get(name, {}).get(value, value)
			out[name] = value if value in f.options else default
		elif f.kind == "roles":
			out[name] = _role_names(value)
		elif f.kind == "data" and name == "login_title":
			text = (value if isinstance(value, str) else "").strip()
			out[name] = (text or default)[:LOGIN_TITLE_MAX]
		else:
			text = value if isinstance(value, str) else ""
			out[name] = text.strip() if text.strip() else (default or "")
	return out


# (label, text field, background field) — checked in light and dark
CONTRAST_PAIRS = (
	("Body text", "text_color", "content_bg"),
	("Muted text", "muted_text", "content_bg"),
	("Header text", "navbar_text", "navbar_bg"),
	("Sidebar text", "sidebar_text", "sidebar_bg"),
	("Sidebar active item", "sidebar_active_text", "sidebar_active_bg"),
	("Primary button", "primary_btn_text", "primary_btn_bg"),
	("Primary button (hover)", "primary_btn_text", "primary_btn_hover"),
	("Secondary button", "secondary_btn_text", "secondary_btn_bg"),
	("Table header", "table_header_text", "table_header_bg"),
	("Table rows", "table_body_text", "table_body_bg"),
	("Number card value", "card_value_text", "card_bg"),
	("Number card label", "card_label_text", "card_bg"),
	("Input text", "input_text", "input_bg"),
	("Input label", "input_label", "content_bg"),
	("Login box text", "login_text", "login_card_bg"),
	("Login button", "login_button_text", "login_button_bg"),
	("Login button (hover)", "login_button_text", "login_button_hover"),
)


def contrast_warnings(raw: dict) -> list[str]:
	"""Human-readable warnings for pairs below WCAG AA (4.5:1). Never blocks a save."""
	s = coerce_settings(raw)
	warnings = []
	for suffix, mode in (("", ""), ("_dark", " (dark mode)")):
		for label, fg, bg in CONTRAST_PAIRS:
			ratio = contrast(s[fg + suffix], s[bg + suffix])
			if ratio < MIN_CONTRAST:
				warnings.append(f"{label}{mode}: contrast {ratio:.1f}:1, aim for {MIN_CONTRAST}:1")
	return warnings


def validate_value(name: str, value):
	"""The one rulebook for a single setting, used by the settings form and by import.

	Returns the cleaned value ('#abc' → '#AABBCC', '1' → 1, legacy 'Center' → 'Default'),
	raises ValueError(reason) when the value is not acceptable, KeyError for an unknown setting.
	"""
	base = name[:-5] if name.endswith("_dark") and name[:-5] in FIELDS else name
	f = FIELDS[base]
	if f.kind == "color":
		color = normalize_hex(value) if isinstance(value, str) else None
		if not color:
			raise ValueError("not a hex colour")
		return color
	if f.kind == "check":
		if value in (0, 1, True, False, "0", "1"):
			return int(value)
		raise ValueError("must be 0 or 1")
	if f.kind == "select":
		value = _LEGACY_SELECT.get(name, {}).get(value, value)
		if value not in f.options:
			raise ValueError("must be one of: " + ", ".join(f.options))
		return value
	if f.kind == "roles":
		if not isinstance(value, list) or not all(isinstance(r, str | dict) for r in value):
			raise ValueError("must be a list of role names")
		return _role_names(value)
	if not isinstance(value, str):
		raise ValueError("must be text")
	value = value.strip()
	limit = f.length or TEXT_MAX.get(f.kind)
	if limit and len(value) > limit:
		raise ValueError(f"longer than {limit} characters")
	if f.kind == "code" and "<" in value:
		raise ValueError("'<' is not allowed")
	if f.kind == "image" and value and not _SAFE_URL.match(value):
		raise ValueError("not a /files/, /assets/ or http(s) URL")
	return value


def cross_field_errors(raw: dict) -> list[str]:
	"""Rules between settings (one field alone cannot break them). Used on save and on import."""
	s = coerce_settings(raw)
	errors = []
	if s["login_background"] == "Image" and not s["login_background_image"]:
		errors.append(
			f"{label_of('login_background_image')}: Background is 'Image' but there is no usable image. "
			"Attach an image uploaded on this site, or set Background to Theme default or Colour."
		)
	return errors
