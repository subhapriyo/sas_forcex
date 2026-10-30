/**
 * ForceX rebrand layer — sas_forcex/public/js/forcex_rebrand.bundle.js
 *
 * Replaces upstream product names with ForceX names in the visible UI.
 * Loaded on every Desk page (app_include_js) and on website pages such as
 * /login (web_include_js) — see hooks.py.
 *
 * Safety rules:
 *  - Never edits anything a user typed or a record value (see SKIP_SELECTOR).
 *  - Case-sensitive, whole-word matching only, so technical identifiers such as
 *    "frappe.client" or "erpnext.selling" are left alone.
 *  - Idempotent: running twice never produces "ForceX ForceX ...", which also
 *    stops the MutationObserver from looping on its own edits.
 *
 * Server-rendered text (emails, PDFs, print formats) is NOT covered by this
 * file; handle those with a translations CSV in the app.
 */
(() => {
	"use strict";

	// Guard against loading twice (e.g. bundle included by two hooks).
	if (window.forcex && window.forcex.rebrandLoaded) return;

	// ---------------------------------------------------------------------
	// 1. Name map
	// ---------------------------------------------------------------------
	// Order matters: more specific phrases come before shorter ones, so
	// "Frappe HR" becomes "ForceX HR" before the bare "Frappe" rule runs.
	//
	// type "phrase": replaced wherever the whole word/phrase appears in text.
	// type "exact":  replaced only when the entire label is that word, because
	//                the bare word also appears inside ordinary labels
	//                (e.g. "Telephony Call Type" must stay as it is).
	const RULES = [
		{ from: "Frappe Framework", to: "ForceX", type: "phrase" },
		{ from: "Frappe Desk", to: "ForceX Desk", type: "phrase" },
		{ from: "Frappe HR", to: "ForceX HR", type: "phrase" },
		{ from: "Frappe Helpdesk", to: "ForceX Helpdesk", type: "phrase" },
		{ from: "Frappe Telephony", to: "ForceX Telephony", type: "phrase" },
		{ from: "ERPNext", to: "ForceX ERP", type: "phrase" },
		{ from: "HRMS", to: "ForceX HR", type: "phrase" },
		{ from: "SAS ForceX", to: "ForceX Service", type: "phrase" },
		{ from: "sas_forcex", to: "ForceX Service", type: "phrase" },
		{ from: "Frappe", to: "ForceX", type: "phrase" },
		{ from: "Helpdesk", to: "ForceX Helpdesk", type: "exact" },
		{ from: "Telephony", to: "ForceX Telephony", type: "exact" },
	];

	const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

	// Whole-word match: not preceded or followed by a letter, digit or "_".
	const PHRASE_RULES = RULES.filter((r) => r.type === "phrase").map((r) => ({
		re: new RegExp(`(?<![\\w])${escapeRe(r.from)}(?![\\w])`, "g"),
		to: r.to,
	}));
	const EXACT_RULES = new Map(
		RULES.filter((r) => r.type === "exact").map((r) => [r.from, r.to])
	);

	// Cheap pre-check so the vast majority of text nodes are skipped quickly.
	const QUICK_TEST = new RegExp(RULES.map((r) => escapeRe(r.from)).join("|"));

	// ---------------------------------------------------------------------
	// 2. Core text replacement (pure function, safe to call anywhere)
	// ---------------------------------------------------------------------
	function rebrandText(text) {
		if (typeof text !== "string" || !text || !QUICK_TEST.test(text)) return text;

		// Exact-label rules: keep surrounding whitespace, swap only the word.
		const trimmed = text.trim();
		if (EXACT_RULES.has(trimmed)) {
			return text.replace(trimmed, EXACT_RULES.get(trimmed));
		}

		let out = text;
		for (const rule of PHRASE_RULES) out = out.replace(rule.re, rule.to);
		return out;
	}

	// ---------------------------------------------------------------------
	// 3. What NOT to touch
	// ---------------------------------------------------------------------
	// Anything a user edits, code, and places where Frappe renders record
	// values (form read-only values, list/report cells, comments, timeline).
	// Add data-forcex-skip to any element to opt it out explicitly.
	const SKIP_SELECTOR = [
		"script", "style", "noscript", "code", "pre",
		"input", "textarea", "select", "[contenteditable]", "[contenteditable='true']",
		".ql-editor", ".ace_editor", ".CodeMirror", ".cm-editor",
		".control-value", ".like-disabled-input", ".static-area",
		".list-row-container .list-row-col",
		".dt-body .dt-cell__content",
		".timeline-content", ".comment-content", ".ql-editor-content",
		"[data-forcex-skip]",
	].join(",");

	// Attributes that show text to users (tooltips, placeholders, a11y labels).
	const TEXT_ATTRS = ["title", "placeholder", "aria-label", "data-original-title", "alt"];

	const isSkipped = (el) => !el || !!el.closest(SKIP_SELECTOR);

	// ---------------------------------------------------------------------
	// 4. DOM processing
	// ---------------------------------------------------------------------
	function processTextNode(node) {
		if (isSkipped(node.parentElement)) return;
		const next = rebrandText(node.nodeValue);
		// Write only on a real change, so our own edits don't re-trigger work.
		if (next !== node.nodeValue) node.nodeValue = next;
	}

	function processAttributes(el) {
		if (isSkipped(el)) return;
		for (const attr of TEXT_ATTRS) {
			const value = el.getAttribute(attr);
			if (value) {
				const next = rebrandText(value);
				if (next !== value) el.setAttribute(attr, next);
			}
		}
	}

	function processTree(root) {
		if (!root) return;
		if (root.nodeType === Node.TEXT_NODE) return processTextNode(root);
		if (root.nodeType !== Node.ELEMENT_NODE) return;

		processAttributes(root);
		const walker = document.createTreeWalker(
			root,
			NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT
		);
		let node = walker.nextNode();
		while (node) {
			if (node.nodeType === Node.TEXT_NODE) processTextNode(node);
			else processAttributes(node);
			node = walker.nextNode();
		}
	}

	// Browser tab title (Frappe sets it on every route change).
	function processTitle() {
		const next = rebrandText(document.title);
		if (next !== document.title) document.title = next;
	}

	// ---------------------------------------------------------------------
	// 5. Hide links to upstream sites (help menu, footers, "Powered by")
	// ---------------------------------------------------------------------
	const UPSTREAM_LINKS = [
		'a[href*="frappe.io"]',
		'a[href*="frappeframework.com"]',
		'a[href*="frappe.school"]',
		'a[href*="frappe.cloud"]',
		'a[href*="erpnext.com"]',
		'a[href*="erpnext.org"]',
		'a[href*="github.com/frappe"]',
	].join(",");

	function injectLinkHidingCss() {
		if (document.getElementById("forcex-rebrand-css")) return;
		const style = document.createElement("style");
		style.id = "forcex-rebrand-css";
		style.textContent = `${UPSTREAM_LINKS} { display: none !important; }`;
		document.head.appendChild(style);
	}

	// ---------------------------------------------------------------------
	// 6. Translate-function hook: catches strings before they reach the DOM
	// ---------------------------------------------------------------------
	// __() is Frappe's translation helper; wrapping it rebrands dialog titles,
	// alerts and labels at the source. Applied once, and re-applied if
	// another script replaces __ later.
	function wrapTranslate() {
		const current = window.__;
		if (typeof current !== "function" || current.forcexWrapped) return;
		const wrapped = function (...args) {
			return rebrandText(current.apply(this, args));
		};
		wrapped.forcexWrapped = true;
		window.__ = wrapped;
	}

	// ---------------------------------------------------------------------
	// 7. Watch for new content (Desk renders pages dynamically)
	// ---------------------------------------------------------------------
	let pending = new Set();
	let scheduled = false;

	function flush() {
		scheduled = false;
		const nodes = pending;
		pending = new Set();
		for (const node of nodes) {
			if (node.isConnected) processTree(node);
		}
		processTitle();
		wrapTranslate();
	}

	function schedule(node) {
		pending.add(node);
		if (!scheduled) {
			scheduled = true;
			requestAnimationFrame(flush); // batch bursts of DOM changes
		}
	}

	function start() {
		wrapTranslate();
		injectLinkHidingCss();
		processTree(document.body);
		processTitle();

		new MutationObserver((mutations) => {
			for (const m of mutations) {
				if (m.type === "childList") m.addedNodes.forEach(schedule);
				else if (m.type === "characterData") schedule(m.target);
				else if (m.type === "attributes") schedule(m.target);
			}
		}).observe(document.body, {
			childList: true,
			subtree: true,
			characterData: true,
			attributes: true,
			attributeFilter: TEXT_ATTRS,
		});

		// Title lives in <head>, outside the body observer.
		const titleEl = document.querySelector("head > title");
		if (titleEl) {
			new MutationObserver(processTitle).observe(titleEl, {
				childList: true,
				characterData: true,
				subtree: true,
			});
		}
	}

	// ---------------------------------------------------------------------
	// 8. Public API + boot
	// ---------------------------------------------------------------------
	// Other ForceX code can call forcex.rebrand("...") for strings it builds.
	window.forcex = Object.assign(window.forcex || {}, {
		rebrand: rebrandText,
		rebrandLoaded: true,
	});

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", start, { once: true });
	} else {
		start();
	}

	// Allow unit tests in Node to import the pure function.
	if (typeof module !== "undefined" && module.exports) {
		module.exports = { rebrandText };
	}
})();
