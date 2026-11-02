"""What the browser receives: the Desk boot config and the website/login <head> snippet."""

from __future__ import annotations

import json

from .colours import LIGHT_TEXT, readable_on
from .css import build_css
from .rules import _SAFE_URL, coerce_settings
from .schema import APPEARANCE, FONTS, LOGIN_APPEARANCE

_DESK_TOGGLES = {
	"hide_list_sidebar": "fxh-hide-list-sidebar",
	"hide_list_likes_comments": "fxh-hide-likes",
	"mobile_card_view": "fxh-mobile-cards",
	"mobile_wrap_content": "fxh-mobile-wrap",
}


def build_config(raw: dict | None, for_login: bool = False, roles=()) -> dict:
	"""Everything the browser needs to apply the theme.

	roles: the current user's roles (for 'Hide search for these roles').
	for_login: add the /login options (position, background, title, panel...).
	"""
	s = coerce_settings(raw)
	if not s["enabled"]:
		return {"enabled": 0, "classes": [], "css": ""}

	classes = ["fxh-on"] + [cls for key, cls in _DESK_TOGGLES.items() if s[key]]
	hide_search = bool(set(s["hide_search_for_roles"]) & set(roles or ()))
	if hide_search:
		classes.append("fxh-hide-search")

	extra = {}
	config = {
		"enabled": 1,
		"classes": classes,
		"appearance": APPEARANCE[s["appearance"]],
		"font_url": FONTS[s["font_family"]][1],
		"hide_help": bool(s["hide_help"]),
		"hide_search": hide_search,
	}
	if for_login:
		config["login"] = _login_options(s, classes, extra)
	config["css"] = build_css(s, extra)
	return config


def _login_options(s, classes, extra):
	"""Login page classes/vars; returns the 'login' block of the config."""
	classes.append("fxh-login")  # scopes every login rule in the stylesheet
	pos = s["login_box_position"].lower()
	if pos != "default":
		classes.append(f"fxh-login-{pos}")
	if s["login_animation"]:
		classes.append("fxh-login-animate")
	if not s["show_login_accent"]:
		classes.append("fxh-login-noaccent")
	if s["login_footer"] != "Theme default":
		classes.append("fxh-login-footer" if s["login_footer"] == "Show" else "fxh-login-nofooter")

	if s["login_background"] == "Colour":
		classes.append("fxh-login-bg-color")
		extra["--fxh-login-bg"] = s["login_background_color"]
		# side-panel text sits on this colour, not on the login box
		extra["--fxh-login-panel-text"] = readable_on(s["login_background_color"])
	elif s["login_background"] == "Image" and _SAFE_URL.match(s["login_background_image"]):
		classes.append("fxh-login-bg-image")
		extra["--fxh-login-bg"] = f'url("{s["login_background_image"]}")'
		extra["--fxh-login-panel-text"] = LIGHT_TEXT

	login = {"title": s["login_title"], "theme": LOGIN_APPEARANCE[s["login_appearance"]]}
	headline, tagline = s["side_panel_headline"], s["side_panel_tagline"]
	if pos != "default" and s["show_side_panel"] and (headline or tagline):
		classes.append("fxh-login-panel")
		if "fxh-login-bg-image" in classes:
			classes.append("fxh-login-fg-shadow")  # white text over a photo
		login["panel"] = {"headline": headline, "tagline": tagline}
	return login


# =====================================================================================
# Website / login <head> snippet
# =====================================================================================
# Runs before the page paints: adds the classes, picks login light/dark, then (once the
# DOM exists) sets the title and builds the side panel. Text is set with textContent,
# never innerHTML. Wrapped in try/catch so a theme problem can never break sign-in.
_HEAD_JS = (
	"(function(c){try{if(!c||!c.enabled)return;var h=document.documentElement;"
	"c.classes.forEach(function(k){h.classList.add(k)});"
	"var L=c.login;if(!L)return;var t=L.theme;"
	"if(t==='auto'){t=window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}"
	"h.setAttribute('data-theme',t);"
	"document.addEventListener('DOMContentLoaded',function(){try{"
	"var hd=document.querySelector('#page-login .for-login .page-card-head h4');"
	"if(hd&&L.title){hd.textContent=L.title;document.title=L.title}"
	"if(!L.panel)return;var host=document.querySelector('#page-login .page_content > div');"
	"if(!host||host.querySelector('.fxh-login-panel-box'))return;"
	"var box=document.createElement('aside');box.className='fxh-login-panel-box';"
	"if(L.panel.headline){var e=document.createElement('h2');e.textContent=L.panel.headline;box.appendChild(e)}"
	"if(L.panel.tagline){var p=document.createElement('p');p.textContent=L.panel.tagline;box.appendChild(p)}"
	"host.appendChild(box)}catch(x){}})}catch(x){}})"
)


def render_head_script(config: dict) -> str:
	"""<style> + optional font <link> + <script> for website pages ('' when disabled)."""
	if not config or not config.get("enabled"):
		return ""
	payload = {k: config[k] for k in ("enabled", "classes", "login") if k in config}
	# '</' inside a <script> would end it early; '<\/' is the same string to JSON.
	data = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
	html = f'<style id="fxh-theme-vars">{config["css"]}</style>'
	if config.get("font_url"):
		html += f'<link rel="stylesheet" id="fxh-theme-font" href="{config["font_url"]}">'
	return html + f"<script>{_HEAD_JS}({data});</script>"
