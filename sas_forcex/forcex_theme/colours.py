"""Colour maths: hex parsing, mixing, WCAG luminance and contrast. No Frappe, no schema."""

from __future__ import annotations

import re

DARK_TEXT = "#0B1C33"  # ForceX deep navy (prototype --deep)
LIGHT_TEXT = "#FFFFFF"

_HEX = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")


def normalize_hex(value, fallback=None):
	"""'#abc' / '0f3870' → '#AABBCC' / '#0F3870'; anything else → fallback."""
	m = _HEX.match((value or "").strip()) if isinstance(value, str) or value is None else None
	if not m:
		return fallback
	h = m.group(1)
	if len(h) == 3:
		h = "".join(c * 2 for c in h)
	return "#" + h.upper()


def _rgb(hex_color):
	h = hex_color.lstrip("#")
	return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
	return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def mix(a, b, weight_b):
	"""Blend colour a toward colour b by weight_b (0..1)."""
	ra, rb = _rgb(a), _rgb(b)
	return _hex(tuple(x + (y - x) * weight_b for x, y in zip(ra, rb, strict=True)))


def luminance(hex_color):
	"""WCAG relative luminance."""

	def ch(c):
		c = c / 255
		return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

	r, g, b = (ch(c) for c in _rgb(hex_color))
	return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
	la, lb = luminance(a), luminance(b)
	return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def readable_on(bg, candidates=(LIGHT_TEXT, DARK_TEXT)):
	"""Pick the candidate text colour with the best contrast on bg."""
	return max(candidates, key=lambda c: contrast(c, bg))


def hover_of(color_):
	"""A hover shade: lighten dark colours, darken light ones."""
	return mix(color_, "#FFFFFF", 0.15) if luminance(color_) < 0.35 else mix(color_, "#000000", 0.10)
