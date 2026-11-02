// ForceX Harbour — Desk side of the ForceX theme.
//
// The server (sas_forcex.theme.extend_bootinfo) puts the theme into
// frappe.boot.forcex_theme:
//   { enabled, classes[], css, appearance: "auto"|"light"|"dark",
//     font_url, hide_help, hide_search }
//
// frappe.boot is set inline in desk.html before app scripts run, and the Desk
// renders only after they load, so applying everything here — at load time —
// means the very first paint is already themed (no flash of the stock look).
//
// Exposed as window.forcex.theme.apply(config) so it can be re-applied and tested.
// Any failure is logged and swallowed: a theme must never break the Desk.
(function () {
	"use strict";

	const STYLE_ID = "fxh-theme-vars";
	const FONT_ID = "fxh-theme-font";

	/** Find an element by id in <head>, or create and append it. */
	function ensureHeadElement(tag, id) {
		let el = document.getElementById(id);
		if (!el) {
			el = document.createElement(tag);
			el.setAttribute("id", id);
			document.head.appendChild(el);
		}
		return el;
	}

	/** The --fxh-* tokens (one block per mode) built by theme_engine.build_css. */
	function applyCss(css) {
		ensureHeadElement("style", STYLE_ID).textContent = css || "";
	}

	/** Load the web font once (only for fonts Frappe does not ship, e.g. IBM Plex Sans). */
	function applyFont(url) {
		if (!url || document.getElementById(FONT_ID)) return;
		const link = ensureHeadElement("link", FONT_ID);
		link.rel = "stylesheet";
		link.href = url;
	}

	/** "Always Light" / "Always Dark": set it now and keep it when Toggle Theme is used. */
	function forceAppearance(mode) {
		if (mode !== "light" && mode !== "dark") return; // "auto" = respect the user's choice
		const root = document.documentElement;
		const pin = () => {
			root.setAttribute("data-theme-mode", mode);
			root.setAttribute("data-theme", mode);
		};
		pin();

		const ui = frappe.ui;
		if (!ui || ui.set_theme?.__fxhForced) return;
		const original = ui.set_theme;
		ui.set_theme = function () {
			if (typeof original === "function") original.call(this, mode);
			pin();
		};
		ui.set_theme.__fxhForced = true;
	}

	/** Remove the "Help" row from the v16 sidebar header menu. */
	function hideHelp() {
		// SidebarHeader.system_items() only adds Help when get_help_siblings()
		// returns something, so an empty answer removes the row cleanly.
		const proto = frappe.ui?.SidebarHeader?.prototype;
		if (!proto || proto.__fxhHelpHidden) return;
		proto.get_help_siblings = () => [];
		proto.__fxhHelpHidden = true;
	}

	/** Apply a theme config. Returns true when the theme was applied. */
	function apply(config) {
		if (!config || !config.enabled) return false;
		try {
			const root = document.documentElement;
			(config.classes || []).forEach((cls) => root.classList.add(cls));
			applyCss(config.css);
			applyFont(config.font_url);
			forceAppearance(config.appearance);
			if (config.hide_help) hideHelp();
			return true;
		} catch (err) {
			console.warn("ForceX theme could not be applied", err);
			return false;
		}
	}

	window.forcex = window.forcex || {};
	window.forcex.theme = { apply };

	apply(window.frappe && frappe.boot && frappe.boot.forcex_theme);
})();
