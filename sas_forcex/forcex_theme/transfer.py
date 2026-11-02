"""Export / import — move a theme between sites (forcex → fleeto → a client tenant).

Import is a dry run first (validate_import → preview) and only then a save, and the
site re-validates on save, so a preview can never be used to smuggle values in.
"""

from __future__ import annotations

import json

from .rules import coerce_settings, contrast_warnings, cross_field_errors, validate_value
from .schema import COLOR_FIELDS, DEFAULTS, label_of

EXPORT_FORMAT = "forcex-theme"
EXPORT_VERSION = 1
IMPORT_MAX_BYTES = 200_000  # a full export is ~5 KB; anything near this is not ours


def export_payload(raw: dict | None, exported_on: str | None = None, site: str | None = None) -> dict:
	"""Every setting (light + dark), cleaned, plus a header that import checks."""
	return {
		"format": EXPORT_FORMAT,
		"version": EXPORT_VERSION,
		"exported_on": exported_on,
		"site": site,
		"settings": coerce_settings(raw),
	}


def parse_import(text: str) -> tuple[dict, list[str]]:
	"""Check an exported file and return (values to apply, human-readable skipped list).

	Only keys present in the file are returned, so a partial file (e.g. just the button
	colours) changes just those. Raises ValueError when the file is not a usable ForceX theme.
	"""
	if not isinstance(text, str) or not text.strip():
		raise ValueError("File is empty.")
	if len(text) > IMPORT_MAX_BYTES:
		raise ValueError("File is too large to be a ForceX theme export.")
	try:
		data = json.loads(text)
	except ValueError:
		raise ValueError("File is not valid JSON.")
	if not isinstance(data, dict) or data.get("format") != EXPORT_FORMAT:
		raise ValueError("File is not a ForceX theme export.")
	version = data.get("version")
	# bool is a subclass of int in Python, so `"version": true` must be refused explicitly
	if isinstance(version, bool) or not isinstance(version, int) or version < 1:
		raise ValueError("File has no valid format version.")
	if version > EXPORT_VERSION:
		raise ValueError(f"File was exported by a newer ForceX version ({version}); update sas_forcex first.")
	settings = data.get("settings")
	if not isinstance(settings, dict):
		raise ValueError("File has no settings.")
	if not settings:
		raise ValueError("File contains no settings.")

	values, skipped = {}, []
	for name, value in settings.items():
		if name not in DEFAULTS:
			skipped.append(f"{name}: unknown setting")
			continue
		try:
			values[name] = validate_value(name, value)
		except ValueError as err:
			skipped.append(f"{label_of(name)}: {err}")
	return values, skipped


def _exists_check(source):
	"""None (= do not check), a callable name -> bool, or any collection of names."""
	if source is None or callable(source):
		return source
	known = set(source)
	return known.__contains__


def validate_import(text: str, current: dict | None, existing_roles=None, existing_files=None) -> dict:
	"""Dry run of an import against the current theme. Nothing is saved.

	existing_roles / existing_files: what exists on this site — a collection of names or a
	callable name -> bool (so the site can look up just what the file mentions); None skips the check.
	Returns {ok, errors, changes, unchanged, skipped, warnings, values}:
	  errors    block the import (bad file, or a result that could not be saved)
	  skipped   single values left out, with the reason; they do not block
	  changes   [{field, label, old, new, is_color}] for the preview
	  warnings  readability problems in the resulting theme
	  values    what an import would write
	"""
	report = {
		"ok": False,
		"errors": [],
		"changes": [],
		"unchanged": 0,
		"skipped": [],
		"warnings": [],
		"values": {},
	}
	try:
		values, skipped = parse_import(text)
	except ValueError as err:
		report["errors"].append(str(err))
		return report

	# --- checks against this site
	role_exists, file_exists = _exists_check(existing_roles), _exists_check(existing_files)
	roles = values.get("hide_search_for_roles")
	if roles is not None and role_exists:
		missing = [r for r in roles if not role_exists(r)]
		skipped += [
			f"{label_of('hide_search_for_roles')}: role '{r}' does not exist on this site" for r in missing
		]
		values["hide_search_for_roles"] = [r for r in roles if r not in missing]
	image = values.get("login_background_image")
	# only our own uploads can be checked; /assets/ ships with apps, http(s) is external
	if image and image.startswith("/files/") and file_exists and not file_exists(image):
		skipped.append(f"{label_of('login_background_image')}: {image} is not on this site")
		del values["login_background_image"]

	# --- the theme as it would be after the import
	current = coerce_settings(current)
	merged = coerce_settings(dict(current, **values))
	report["errors"] += cross_field_errors(merged)

	for name, new in values.items():
		old = current[name]
		if old == new:
			report["unchanged"] += 1
		else:
			report["changes"].append(
				{
					"field": name,
					"label": label_of(name),
					"old": old,
					"new": new,
					"is_color": name in COLOR_FIELDS,
				}
			)

	report.update(skipped=skipped, warnings=contrast_warnings(merged), values=values, ok=not report["errors"])
	return report
