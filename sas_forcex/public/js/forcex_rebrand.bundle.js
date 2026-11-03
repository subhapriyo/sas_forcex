/**
 * ForceX rebrand layer — sas_forcex/public/js/forcex_rebrand.bundle.js
 *
 * Replaces upstream product names with ForceX names in the visible UI.
 * Loaded on every Desk page (app_include_js) and on website pages such as
 * /login (web_include_js) — see hooks.py.
 *
 * Safety rules:
 *  - Never edits anything a user typed or a record value (see ALWAYS_SKIP and
 *    RECORD_CELLS). One exception: list cells of the Desk's own navigation records
 *    (Workspace, Sidebar, ... see LABEL_DOCTYPES), whose names are menu labels.
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
	// values (form read-only values, comments, timeline).
	// Add data-forcex-skip to any element to opt it out explicitly.
	const ALWAYS_SKIP = [
		"script", "style", "noscript", "code", "pre",
		"input", "textarea", "select", "[contenteditable]", "[contenteditable='true']",
		".ql-editor", ".ace_editor", ".CodeMirror", ".cm-editor",
		".control-value", ".like-disabled-input", ".static-area",
		".timeline-content", ".comment-content", ".ql-editor-content",
		"[data-forcex-skip]",
	].join(",");

	// List and report cells show record values, so they are skipped too...
	const RECORD_CELLS = [".list-row-container .list-row-col", ".dt-body .dt-cell__content"].join(",");

	// ...except on lists of these doctypes. Their records are the Desk's own menus
	// (e.g. the "ERPNext Settings" workspace at /desk/build/workspace), so their
	// names are labels people read, not business data. The record itself and its
	// URL keep the upstream name; only what is shown changes.
	const LABEL_DOCTYPES = new Set([
		"Workspace", "Workspace Sidebar", "Sidebar", "Desktop Icon", "Module Def", "Dock",
	]);

	/** Doctype of the list/report view on screen (null elsewhere). */
	function currentListDoctype() {
		const list = window.cur_list;
		if (list && list.doctype) return list.doctype;
		const route = window.frappe && typeof frappe.get_route === "function" ? frappe.get_route() : [];
		return route && route[0] === "List" ? route[1] : null;
	}

	// Attributes that show text to users (tooltips, placeholders, a11y labels).
	const TEXT_ATTRS = ["title", "placeholder", "aria-label", "data-original-title", "alt"];

	function isSkipped(el) {
		if (!el || el.closest(ALWAYS_SKIP)) return true;
		if (el.closest(RECORD_CELLS)) return !LABEL_DOCTYPES.has(currentListDoctype());
		return false;
	}

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

		unwrapDocLinks(root);
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
	// 5. Hide upstream links, videos and video images
	// ---------------------------------------------------------------------
	// Links to upstream sites (help menu, footers, "Powered by", docs links).
	const UPSTREAM_LINKS = [
		'a[href*="frappe.io"]',
		'a[href*="frappeframework.com"]',
		'a[href*="frappe.school"]',
		'a[href*="frappe.cloud"]',
		'a[href*="erpnext.com"]',
		'a[href*="erpnext.org"]',
		'a[href*="github.com/frappe"]',
		'a[href*="youtube.com"]',
		'a[href*="youtu.be"]',
	];

	// Upstream tutorial videos and their images:
	//  - onboarding steps ("Get your books ready" etc.) show a YouTube thumbnail with a
	//    play button and open a YouTube player; hiding the whole media column lets the
	//    step text use the full width (its grid column is `auto`, so it collapses);
	//  - workspace link cards can open a YouTube help video;
	//  - Frappe's help video dialog (Plyr with the YouTube provider);
	//  - any embedded YouTube / Vimeo player, YouTube thumbnail, or ERPNext's own
	//    video placeholder / YouTube icon images.
	// Only these exact targets: an ordinary <img>, <iframe> or link is never hidden.
	const UPSTREAM_MEDIA = [
		".onboarding-step-media",
		".onboarding-video",
		".onboarding-video-player",
		".help-video-link",
		".link-item:has(.help-video-link)",
		'.video-player[data-plyr-provider="youtube"]',
		'.video-player[data-plyr-provider="vimeo"]',
		'iframe[src*="youtube.com"]',
		'iframe[src*="youtube-nocookie.com"]',
		'iframe[src*="youtu.be"]',
		'iframe[src*="vimeo.com"]',
		'img[src*="ytimg.com"]',
		'img[src*="img.youtube.com"]',
		'img[src*="erpnext-video-placeholder"]',
		'img[src*="YouTube-icon"]',
	];

	/** The stylesheet text that hides everything above. */
	function hidingCss() {
		return `${[...UPSTREAM_LINKS, ...UPSTREAM_MEDIA].join(",\n")} { display: none !important; }`;
	}

	function injectHidingCss() {
		if (document.getElementById("forcex-rebrand-css")) return;
		const style = document.createElement("style");
		style.id = "forcex-rebrand-css";
		style.textContent = hidingCss();
		document.head.appendChild(style);
	}

	// Upstream docs sites. Inside onboarding step text ("See [Chart of Accounts](...)."),
	// hiding the link would leave "See .", so the link is replaced by its own text.
	const DOC_HOSTS = /(^|\.)(frappe\.io|frappeframework\.com|erpnext\.com|erpnext\.org)$/;
	const DOC_TEXT_LINKS = ".onboarding-step-description a[href]";

	function isUpstreamDocLink(href) {
		try {
			return DOC_HOSTS.test(new URL(href, "https://local.invalid").hostname);
		} catch (e) {
			return false;
		}
	}

	/** Turn upstream docs links inside onboarding descriptions into plain text. */
	function unwrapDocLinks(root) {
		if (!root || typeof root.querySelectorAll !== "function") return;
		const links = [...root.querySelectorAll(DOC_TEXT_LINKS)];
		if (typeof root.matches === "function" && root.matches(DOC_TEXT_LINKS)) links.push(root);
		for (const link of links) {
			if (isUpstreamDocLink(link.href)) {
				link.replaceWith(document.createTextNode(link.textContent));
			}
		}
	}

	/**
	 * Switch off Frappe's help video dialog (frappe.help, Desk only), so no code path can
	 * still open a YouTube player after its link or button is hidden.
	 */
	function muteUpstreamVideos() {
		const help = window.frappe && frappe.help;
		if (!help || help.forcexMuted) return;
		help.show_video = () => {};
		help.show = () => {};
		help.has_help = () => false;
		help.forcexMuted = true;
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
		injectHidingCss();
		muteUpstreamVideos();
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
		module.exports = { rebrandText, isSkipped, hidingCss, muteUpstreamVideos, unwrapDocLinks };
	}
})();
