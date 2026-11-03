/**
 * Unit tests for public/js/forcex_rebrand.bundle.js — upstream names → ForceX names.
 *
 * Run:  node --test sas_forcex/tests_js/*.test.cjs   (from apps/sas_forcex; Node 18+, no npm packages)
 *
 * rebrandText() is a pure function, so most tests call it directly. The bundle
 * also exports it for Node (module.exports) — in the browser it is forcex.rebrand.
 */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const BUNDLE = path.join(__dirname, "..", "public", "js", "forcex_rebrand.bundle.js");

/** Load the bundle as Node would, with just enough browser globals for it to boot. */
function loadRebrand(globals = {}) {
  const listeners = [];
  const sandbox = {
    module: { exports: {} },
    document: { readyState: "loading", addEventListener: (type, fn) => listeners.push(type) },
    URL, // a browser global that vm sandboxes do not provide
    ...globals,
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(BUNDLE, "utf8"), sandbox);
  const exp = sandbox.module.exports;
  return { ...exp, forcex: sandbox.forcex, listeners, sandbox };
}

/** A fake element that sits inside the given CSS selectors (enough for el.closest). */
function elementInside(...selectors) {
  return {
    closest: (list) => (list.split(",").some((s) => selectors.includes(s.trim())) ? {} : null),
  };
}
const LIST_CELL = ".list-row-container .list-row-col";
const REPORT_CELL = ".dt-body .dt-cell__content";

const { rebrandText } = loadRebrand();

/* ---------- the name map ------------------------------------------------------ */
const CASES = [
  // [shown upstream,           expected ForceX text]
  ["Frappe Framework", "ForceX"],
  ["Powered by Frappe", "Powered by ForceX"],
  ["Login to Frappe Desk", "Login to ForceX Desk"],
  ["ERPNext Settings", "ForceX ERP Settings"],
  ["Frappe HR", "ForceX HR"],
  ["HRMS", "ForceX HR"],
  ["SAS ForceX", "ForceX Service"],
  ["sas_forcex", "ForceX Service"],
  ["ERPNext and Frappe HR", "ForceX ERP and ForceX HR"],
  ["Helpdesk", "ForceX Helpdesk"], // exact label
  ["  Telephony ", "  ForceX Telephony "], // exact label, spacing kept
];
for (const [input, expected] of CASES) {
  test(`rebrands ${JSON.stringify(input)}`, () => assert.equal(rebrandText(input), expected));
}

/* ---------- what must NOT change ------------------------------------------------- */
const UNCHANGED = [
  "Telephony Call Type", // bare word inside a longer label
  "Helpdesk Settings",
  "frappe.client.get", // technical identifiers (case-sensitive)
  "erpnext.selling",
  "FrappeHR", // not a whole word
  "Sales Invoice", // no brand at all
  "",
];
for (const input of UNCHANGED) {
  test(`leaves ${JSON.stringify(input)} alone`, () => assert.equal(rebrandText(input), input));
}

test("non-string values pass through untouched", () => {
  for (const value of [null, undefined, 42]) assert.equal(rebrandText(value), value);
});

/* ---------- idempotent: protects the MutationObserver from loops ---------------- */
test("running twice changes nothing more", () => {
  for (const [input] of CASES) {
    const once = rebrandText(input);
    assert.equal(rebrandText(once), once, `"${input}" changed again on the second pass`);
  }
});

test("never produces a doubled brand", () => {
  for (const [input] of CASES) assert.ok(!rebrandText(rebrandText(input)).includes("ForceX ForceX"));
});

/* ---------- record cells: only the Desk's own navigation records ------------------ */
// The Workspace list (/desk/build/workspace) shows records such as "ERPNext Settings";
// their names are menu labels, not business data, so they are rebranded too.
for (const doctype of ["Workspace", "Workspace Sidebar", "Sidebar", "Desktop Icon", "Module Def", "Dock"]) {
  test(`list cells of ${doctype} are rebranded`, () => {
    const { isSkipped } = loadRebrand({ cur_list: { doctype } });
    assert.equal(isSkipped(elementInside(LIST_CELL)), false);
    assert.equal(isSkipped(elementInside(REPORT_CELL)), false);
  });
}

test("list cells of business records are never touched", () => {
  for (const doctype of ["Sales Invoice", "Customer", "Item"]) {
    const { isSkipped } = loadRebrand({ cur_list: { doctype } });
    assert.equal(isSkipped(elementInside(LIST_CELL)), true, doctype);
  }
});

test("outside a list view, record cells stay untouched", () => {
  const { isSkipped } = loadRebrand();
  assert.equal(isSkipped(elementInside(LIST_CELL)), true);
});

test("the list doctype can come from the route when cur_list is not set yet", () => {
  const frappe = { get_route: () => ["List", "Workspace", "List"] };
  const { isSkipped } = loadRebrand({ frappe });
  assert.equal(isSkipped(elementInside(LIST_CELL)), false);
});

test("inputs and editors stay untouched even inside a Workspace list", () => {
  const { isSkipped } = loadRebrand({ cur_list: { doctype: "Workspace" } });
  assert.equal(isSkipped(elementInside(LIST_CELL, "input")), true);
  assert.equal(isSkipped(elementInside(LIST_CELL, "[data-forcex-skip]")), true);
});

test("ordinary page text is rebranded and a missing element is skipped", () => {
  const { isSkipped } = loadRebrand();
  assert.equal(isSkipped(elementInside()), false);
  assert.equal(isSkipped(null), true);
});

/* ---------- upstream videos and video images ------------------------------------- */
// What the hiding stylesheet must cover: where Frappe / ERPNext show YouTube media.
const MUST_HIDE = [
  ".onboarding-step-media", // onboarding step: YouTube thumbnail + player column
  ".onboarding-video",
  ".onboarding-video-player",
  ".help-video-link", // workspace link cards that open a YouTube help video
  '.video-player[data-plyr-provider="youtube"]', // Frappe's help video dialog
  'iframe[src*="youtube.com"]',
  'iframe[src*="youtube-nocookie.com"]',
  'iframe[src*="vimeo.com"]',
  'img[src*="ytimg.com"]', // YouTube thumbnails
  'img[src*="img.youtube.com"]',
  'img[src*="erpnext-video-placeholder"]', // ERPNext's own video images
  'img[src*="YouTube-icon"]',
  'a[href*="youtube.com"]',
  'a[href*="youtu.be"]',
  'a[href*="frappe.io"]', // existing: links to upstream sites
  'a[href*="erpnext.com"]',
];

test("the hiding stylesheet covers every upstream video and video image", () => {
  const { hidingCss } = loadRebrand();
  const css = hidingCss();
  for (const selector of MUST_HIDE) assert.ok(css.includes(selector), `missing ${selector}`);
  assert.match(css, /display:\s*none\s*!important/);
});

test("ordinary images and iframes are never hidden", () => {
  const { hidingCss } = loadRebrand();
  const selectors = hidingCss().split("{")[0].split(",").map((s) => s.trim());
  for (const bare of ["img", "iframe", "video", "a"]) assert.ok(!selectors.includes(bare), `bare ${bare}`);
});

test("Frappe's help video dialog is switched off", () => {
  const shown = [];
  const help = { youtube_id: { Item: "abc" }, show_video: (id) => shown.push(id), has_help: () => true };
  const { muteUpstreamVideos } = loadRebrand({ frappe: { help } });
  muteUpstreamVideos();
  help.show_video("https://youtu.be/Swos5xEU0w0");
  help.show("Item");
  assert.equal(shown.length, 0);
  assert.equal(help.has_help("Item"), false);
});

/* ---------- docs links inside onboarding text ----------------------------------- */
// "See [Chart of Accounts](https://docs.frappe.io/...)." — hiding the link left "See .",
// so inside onboarding step descriptions the link becomes plain text instead.
function fakeLink(href, text) {
  return { href, textContent: text, replacedWith: null, replaceWith(node) { this.replacedWith = node; } };
}
function fakeRoot(links) {
  return { querySelectorAll: (sel) => (sel.includes(".onboarding-step-description") ? links : []) };
}
const textDoc = { createTextNode: (t) => ({ text: t }) };

test("upstream docs links in onboarding text become plain text", () => {
  const { unwrapDocLinks, sandbox } = loadRebrand();
  sandbox.document = textDoc;
  const docs = fakeLink("https://docs.frappe.io/erpnext/user/manual/en/chart-of-accounts", "Chart of Accounts");
  const hr = fakeLink("https://docs.frappe.io/hr/appraisal", "Appraisal");
  unwrapDocLinks(fakeRoot([docs, hr]));
  assert.equal(docs.replacedWith.text, "Chart of Accounts");
  assert.equal(hr.replacedWith.text, "Appraisal");
});

test("links to the site's own pages stay links", () => {
  const { unwrapDocLinks, sandbox } = loadRebrand();
  sandbox.document = textDoc;
  const own = fakeLink("/desk/account", "Account");
  const other = fakeLink("https://example.com/help", "Help");
  unwrapDocLinks(fakeRoot([own, other]));
  assert.equal(own.replacedWith, null);
  assert.equal(other.replacedWith, null);
});

test("unwrapping is harmless on text nodes and empty input", () => {
  const { unwrapDocLinks } = loadRebrand();
  assert.doesNotThrow(() => unwrapDocLinks(null));
  assert.doesNotThrow(() => unwrapDocLinks({ nodeValue: "text" }));
});

test("muting videos is harmless outside the Desk (no frappe.help)", () => {
  const { muteUpstreamVideos } = loadRebrand();
  assert.doesNotThrow(() => muteUpstreamVideos());
});

/* ---------- upstream logos inside pages ------------------------------------------ */
// Pages such as HRMS's Roster draw upstream logos themselves; the server sends the map
// (frappe.boot.forcex_brand on the Desk, window.forcex_brand on standalone pages).
const HR_UP = "/assets/hrms/images/frappe-hr-logo.svg";
const HR_FX = "/assets/sas_forcex/images/forcex-hr-logo.svg";
const SWAPS = { [HR_UP]: HR_FX };

test("an upstream logo <img> is pointed at the ForceX logo", () => {
  const { swapLogoSrc } = loadRebrand({ location: { origin: "http://site.localhost:8000" } });
  assert.equal(swapLogoSrc(HR_UP, SWAPS), HR_FX);
  assert.equal(swapLogoSrc(`http://site.localhost:8000${HR_UP}`, SWAPS), HR_FX);
  assert.equal(swapLogoSrc(`${HR_UP}?v=3`, SWAPS), HR_FX, "cache-busting query");
});

test("other images keep their source", () => {
  const { swapLogoSrc } = loadRebrand({ location: { origin: "http://site.localhost:8000" } });
  assert.equal(swapLogoSrc("/files/company-logo.png", SWAPS), null);
  assert.equal(swapLogoSrc("", SWAPS), null);
  assert.equal(swapLogoSrc(HR_UP, {}), null);
});

test("inline SVG logos are painted over with CSS, without touching the page's DOM", () => {
  const { inlineLogoCss } = loadRebrand();
  const selector = 'svg[viewBox="0 0 117 117"]:has(path[fill="#A1EEC9"])';
  const css = inlineLogoCss([{ selector, logo: HR_FX }]);
  assert.ok(css.includes(`${selector} {`));
  assert.ok(css.includes(`url("${HR_FX}")`));
  assert.ok(css.includes(`${selector} > *`), "the upstream drawing is hidden");
  assert.equal(inlineLogoCss([]), "");
  assert.equal(inlineLogoCss(undefined), "");
});

test("the brand map comes from the standalone page, else from the Desk boot", () => {
  const page = loadRebrand({ forcex_brand: { logo_swaps: SWAPS } });
  assert.equal(page.brandConfig().logo_swaps[HR_UP], HR_FX);
  const desk = loadRebrand({ frappe: { boot: { forcex_brand: { logo_swaps: SWAPS } } } });
  assert.equal(desk.brandConfig().logo_swaps[HR_UP], HR_FX);
  assert.equal(Object.keys(loadRebrand().brandConfig()).length, 0);
});

/* ---------- boot behaviour ------------------------------------------------------- */
test("exposes forcex.rebrand and waits for the page before touching the DOM", () => {
  const { forcex, listeners } = loadRebrand();
  assert.equal(typeof forcex.rebrand, "function");
  assert.ok(forcex.rebrandLoaded);
  assert.deepEqual(listeners, ["DOMContentLoaded"]);
});
