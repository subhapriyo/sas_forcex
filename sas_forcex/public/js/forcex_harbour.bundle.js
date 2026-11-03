// ForceX Harbour — Desk side of the ForceX theme and brand.
//
// The server (sas_forcex.theme.extend_bootinfo) puts two things into the boot:
//   frappe.boot.forcex_theme  { enabled, classes[], css, appearance: "auto"|"light"|"dark",
//                               font_url, hide_help, hide_search, hide_desktop_menu[] }
//   frappe.boot.forcex_brand  { app_logos: { app_name: logo_url } }   (always, even with
//                               the theme off — the ForceX ERP logo is the brand)
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

	/** Is this Dropdown trigger the desktop page's avatar ($(".desktop-avatar") or the element)? */
	function isDesktopAvatar(trigger) {
		const el = trigger && (trigger.jquery ? trigger[0] : trigger);
		return !!(el && typeof el.matches === "function" && el.matches(".desktop-avatar"));
	}

	/**
	 * Drop rows (e.g. "About", "Frappe Support") from the desktop page's avatar menu.
	 *
	 * frappe/desk/page/desktop/desktop.js builds that menu in a local list and hands it
	 * straight to `new frappe.ui.Dropdown(...)`, so the only place to filter it is that
	 * constructor. The subclass changes nothing for any other dropdown, and stays a
	 * frappe.ui.Dropdown for instanceof checks. (Help-menu rows are hidden on the server.)
	 */
	function hideDesktopMenuRows(labels) {
		const ui = frappe.ui;
		const Base = ui && ui.Dropdown;
		if (!labels || !labels.length || !Base || Base.__fxhWrapped) return;
		// Rows arrive already translated, so match the label and its translation.
		const translate = (s) => (typeof __ === "function" ? __(s) : s);
		const drop = new Set(labels.flatMap((label) => [label, translate(label)]));

		class ForceXDropdown extends Base {
			constructor(opts) {
				if (opts && isDesktopAvatar(opts.trigger) && Array.isArray(opts.options)) {
					opts = { ...opts, options: opts.options.filter((row) => !drop.has(row && row.label)) };
				}
				super(opts);
			}
		}
		ForceXDropdown.__fxhWrapped = true;
		ui.Dropdown = ForceXDropdown;
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
			hideDesktopMenuRows(config.hide_desktop_menu);
			return true;
		} catch (err) {
			console.warn("ForceX theme could not be applied", err);
			return false;
		}
	}

	// ------------------------------------------------------------------ brand: app logos
	// Mirrors sas_forcex/forcex_theme/branding.py → brand_app_data. The server already
	// swapped the logos in the boot; this repeats it for app data the Desk fetches again
	// later (workspace.js assigns a fresh frappe.boot.app_data after a workspace edit).

	/** A copy of app_data with ForceX logos; a [light, dark] pair is replaced as a pair. */
	function brandAppData(appData, logos) {
		if (!Array.isArray(appData)) return appData;
		return appData.map((app) => {
			const logo = app && logos[app.app_name];
			if (!logo) return app;
			const current = app.app_logo_url;
			return { ...app, app_logo_url: Array.isArray(current) ? current.map(() => logo) : logo };
		});
	}

	/** Brand frappe.boot.app_data now, and every time something assigns a new one. */
	function applyBrand(brand) {
		const logos = brand && brand.app_logos;
		const boot = window.frappe && frappe.boot;
		if (!logos || !boot) return false;
		try {
			let current = brandAppData(boot.app_data, logos);
			Object.defineProperty(boot, "app_data", {
				configurable: true,
				enumerable: true,
				get: () => current,
				set: (value) => {
					current = brandAppData(value, logos);
				},
			});
			return true;
		} catch (err) {
			console.warn("ForceX logos could not be applied", err);
			return false;
		}
	}

	window.forcex = window.forcex || {};
	window.forcex.theme = { apply };
	window.forcex.brand = { apply: applyBrand, brandAppData };

	const boot = window.frappe && frappe.boot;
	applyBrand(boot && boot.forcex_brand);
	apply(boot && boot.forcex_theme);
})();
