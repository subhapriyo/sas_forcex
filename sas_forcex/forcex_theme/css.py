"""CSS output: the --fxh-* tokens for each mode, the <style> text, and the default
palette baked into forcex_harbour.bundle.css as a safety net."""

from __future__ import annotations

from .colours import mix, readable_on
from .rules import coerce_settings
from .schema import DEFAULTS, FONTS, PAIRED_COLORS, RADIUS


def _var(name):
	return "--fxh-" + name.replace("_", "-")


def build_vars(raw: dict, mode: str) -> dict[str, str]:
	"""All --fxh-* tokens for one mode ('light' or 'dark')."""
	s = coerce_settings(raw)
	sfx = "_dark" if mode == "dark" else ""
	v = {_var(name): s[name + sfx] for name in PAIRED_COLORS}

	accent = s["accent_color"]
	v["--fxh-primary"] = s["primary_color"]
	v["--fxh-accent"] = accent
	v["--fxh-on-accent"] = readable_on(accent)

	# Pressed states sit one step beyond hover
	for key in ("primary_btn", "login_button"):
		v[_var(key + "_active")] = mix(s[f"{key}_hover{sfx}"], "#000000", 0.12)
	v["--fxh-secondary-btn-active"] = mix(s["secondary_btn_hover" + sfx], s["secondary_btn_text" + sfx], 0.08)

	# Muted / hover shades for the two navigation surfaces, so Frappe's own grey tokens
	# can be remapped inside them and stay readable whatever colour is picked.
	for area in ("navbar", "sidebar"):
		bg, fg = s[f"{area}_bg{sfx}"], s[f"{area}_text{sfx}"]
		v[_var(area + "_muted")] = mix(fg, bg, 0.3)
		v[_var(area + "_hover")] = mix(bg, fg, 0.08)

	focus = s["input_focus" + sfx]
	v["--fxh-ring"] = mix(focus, "#FFFFFF" if mode == "light" else "#000000", 0.45)
	v["--fxh-radius"] = RADIUS[s["corner_style"]]
	v["--fxh-font"] = FONTS[s["font_family"]][0]
	return v


def _block(selector, variables):
	return selector + "{" + ";".join(f"{k}:{val}" for k, val in variables.items()) + "}"


def default_tokens_css() -> str:
	"""The default palette as CSS, baked into forcex_harbour.bundle.css by the generator.

	Safety net: if the per-site <style id="fxh-theme-vars"> is missing (server not
	restarted, cached boot, script blocked) the stylesheet still has every token, so
	nothing renders blank. Selectors are one step less specific than build_css()
	(.fxh-on vs html.fxh-on), so saved settings always win, whatever the load order.
	"""
	blocks = []
	for selector, mode in (
		('.fxh-on:not([data-theme="dark"])', "light"),
		('.fxh-on[data-theme="dark"]', "dark"),
	):
		lines = "".join(f"\t{k}: {v};\n" for k, v in build_vars(DEFAULTS, mode).items())
		blocks.append(f"{selector} {{\n{lines}}}\n")
	return "".join(blocks)


def sanitize_custom_css(css: str) -> str:
	"""Custom CSS is written inside <style>; '<' is the only character that can escape it."""
	return (css or "").replace("<", "")


def build_css(raw: dict, extra_vars: dict | None = None) -> str:
	s = coerce_settings(raw)
	parts = [
		_block('html.fxh-on:not([data-theme="dark"])', build_vars(s, "light")),
		_block('html.fxh-on[data-theme="dark"]', build_vars(s, "dark")),
	]
	if extra_vars:
		parts.append(_block("html.fxh-on", extra_vars))
	custom = sanitize_custom_css(s["custom_css"]).strip()
	if custom:
		parts.append("/* ForceX Theme Settings → Custom CSS */\n" + custom)
	return "\n".join(parts)
