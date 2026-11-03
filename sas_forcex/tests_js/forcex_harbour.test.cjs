/**
 * Unit tests for public/js/forcex_harbour.bundle.js — the Desk side of the ForceX theme.
 *
 * Run:  node --test sas_forcex/tests_js/*.test.cjs   (from apps/sas_forcex; Node 18+, no npm packages)
 *
 * The bundle reads frappe.boot.forcex_theme (built by sas_forcex.theme.extend_bootinfo) and
 * applies it to <html>. We run it in a sandbox with a tiny fake document and a fake frappe,
 * so the tests check OUR logic: classes, the <style> tag, forced light/dark, the Help row.
 * Written before the bundle was refactored (TDD).
 */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const BUNDLE = path.join(__dirname, "..", "public", "js", "forcex_harbour.bundle.js");

/* ---------- a fake DOM just big enough for the bundle --------------------------- */
function makeElement(tag) {
  const attrs = {};
  return {
    tagName: tag.toUpperCase(),
    id: "",
    textContent: "",
    rel: "",
    href: "",
    setAttribute(k, v) { attrs[k] = String(v); if (k === "id") this.id = String(v); },
    getAttribute(k) { return k in attrs ? attrs[k] : null; },
  };
}

function makeDocument(theme = "light") {
  const byId = {};
  const head = {
    children: [],
    appendChild(el) { this.children.push(el); if (el.id) byId[el.id] = el; return el; },
  };
  const root = makeElement("html");
  root.setAttribute("data-theme", theme);
  root.setAttribute("data-theme-mode", theme);
  const classes = new Set();
  root.classList = { add: (c) => classes.add(c), contains: (c) => classes.has(c), _set: classes };
  return {
    documentElement: root,
    head,
    createElement: makeElement,
    getElementById: (id) => byId[id] || head.children.find((e) => e.id === id) || null,
  };
}

/** A stand-in for frappe.ui.Dropdown that remembers the options it was built with. */
class FakeDropdown {
  constructor(opts) { this.opts = opts; FakeDropdown.built.push(opts); }
}
FakeDropdown.built = [];

/** Something that looks like $(selector) for the given CSS class. */
const jq = (cls) => ({ jquery: "3.7", 0: { matches: (sel) => sel === `.${cls}` }, length: 1 });

/** Load the bundle with a given boot config. Returns handles for assertions. */
function load(config, { theme = "light", boot = {} } = {}) {
  const document = makeDocument(theme);
  class SidebarHeader {
    get_help_siblings() { return [{ group: "", options: ["docs"] }]; }
  }
  const setThemeCalls = [];
  FakeDropdown.built = [];
  const frappe = {
    boot: config === undefined ? { ...boot } : { forcex_theme: config, ...boot },
    ui: { SidebarHeader, set_theme: (t) => setThemeCalls.push(t), Dropdown: FakeDropdown },
  };
  const sandbox = { document, frappe, console };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(BUNDLE, "utf8"), sandbox);
  return { sandbox, document, root: document.documentElement, frappe, SidebarHeader, setThemeCalls };
}

const ON = (extra = {}) => ({ enabled: 1, classes: ["fxh-on"], css: "html.fxh-on{--fxh-x:#000}", appearance: "auto", ...extra });

/* ---------- safe no-ops ---------------------------------------------------------- */
test("does nothing (and does not throw) when the boot has no theme", () => {
  const { root, document } = load(undefined);
  assert.equal(root.classList._set.size, 0);
  assert.equal(document.head.children.length, 0);
});

test("a disabled theme leaves the Desk untouched", () => {
  const { root, document } = load({ enabled: 0, classes: [], css: "" });
  assert.equal(root.classList._set.size, 0);
  assert.equal(document.head.children.length, 0);
});

/* ---------- classes and colour tokens -------------------------------------------- */
test("adds the theme classes to <html>", () => {
  const { root } = load(ON({ classes: ["fxh-on", "fxh-hide-likes"] }));
  assert.ok(root.classList.contains("fxh-on"));
  assert.ok(root.classList.contains("fxh-hide-likes"));
});

test("writes the colour tokens into a single <style id=fxh-theme-vars>", () => {
  const { sandbox, document } = load(ON());
  const style = document.getElementById("fxh-theme-vars");
  assert.equal(style.textContent, "html.fxh-on{--fxh-x:#000}");
  // applying again (e.g. after a settings save) must reuse the tag, not add another
  sandbox.forcex.theme.apply(ON({ css: "html.fxh-on{--fxh-x:#fff}" }));
  const styles = document.head.children.filter((e) => e.id === "fxh-theme-vars");
  assert.equal(styles.length, 1);
  assert.equal(styles[0].textContent, "html.fxh-on{--fxh-x:#fff}");
});

test("loads the web font once", () => {
  const { sandbox, document } = load(ON({ font_url: "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans" }));
  sandbox.forcex.theme.apply(ON({ font_url: "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans" }));
  const links = document.head.children.filter((e) => e.tagName === "LINK");
  assert.equal(links.length, 1);
  assert.equal(links[0].rel, "stylesheet");
});

/* ---------- forced appearance ---------------------------------------------------- */
test("'Always Dark' switches the Desk to dark and keeps it there", () => {
  const { root, frappe } = load(ON({ appearance: "dark" }), { theme: "light" });
  assert.equal(root.getAttribute("data-theme"), "dark");
  assert.equal(root.getAttribute("data-theme-mode"), "dark");
  frappe.ui.set_theme("light"); // the user's theme switcher tries to change it
  assert.equal(root.getAttribute("data-theme"), "dark");
});

test("'Follow user preference' leaves the user's choice alone", () => {
  const { root, frappe, setThemeCalls } = load(ON({ appearance: "auto" }), { theme: "light" });
  assert.equal(root.getAttribute("data-theme"), "light");
  frappe.ui.set_theme("dark");
  assert.deepEqual(setThemeCalls, ["dark"], "the original set_theme still runs");
});

/* ---------- Help row ------------------------------------------------------------- */
test("hide_help empties the sidebar header's Help submenu", () => {
  const { SidebarHeader } = load(ON({ hide_help: true }));
  const sections = new SidebarHeader().get_help_siblings();
  // (an array from inside the VM has a different Array prototype, so compare shape, not identity)
  assert.ok(Array.isArray(sections));
  assert.equal(sections.length, 0);
});

test("Help stays when hide_help is off", () => {
  const { SidebarHeader } = load(ON({ hide_help: false }));
  assert.equal(new SidebarHeader().get_help_siblings().length, 1);
});

/* ---------- ForceX ERP logo --------------------------------------------------------- */
const ERPNEXT_LOGO = "/assets/erpnext/images/erpnext-logo.svg";
const FORCEX_ERP = "/assets/sas_forcex/images/forcex-erp-logo.svg";
const BRAND = { forcex_brand: { app_logos: { erpnext: FORCEX_ERP } } };
const appData = () => [
  { app_name: "erpnext", app_title: "ERPNext", app_logo_url: ERPNEXT_LOGO },
  { app_name: "hrms", app_title: "Frappe HR", app_logo_url: "/assets/hrms/images/frappe-hr-logo.svg" },
];

test("the ERPNext icon becomes the ForceX ERP icon on load", () => {
  const { frappe } = load(ON(), { boot: { ...BRAND, app_data: appData() } });
  assert.equal(frappe.boot.app_data[0].app_logo_url, FORCEX_ERP);
  assert.equal(frappe.boot.app_data[1].app_logo_url, "/assets/hrms/images/frappe-hr-logo.svg");
});

test("app data the Desk fetches again later (e.g. after editing a workspace) is branded too", () => {
  const { frappe } = load(ON(), { boot: { ...BRAND, app_data: [] } });
  frappe.boot.app_data = appData(); // what workspace.js does with a fresh payload
  assert.equal(frappe.boot.app_data[0].app_logo_url, FORCEX_ERP);
});

test("the logo is part of the brand, so it is swapped even with the theme switched off", () => {
  const { frappe } = load({ enabled: 0, classes: [], css: "" }, { boot: { ...BRAND, app_data: appData() } });
  assert.equal(frappe.boot.app_data[0].app_logo_url, FORCEX_ERP);
});

test("a light/dark logo pair is swapped as a pair", () => {
  const pair = [{ app_name: "erpnext", app_logo_url: [ERPNEXT_LOGO, "/dark.svg"] }];
  const { frappe } = load(ON(), { boot: { ...BRAND, app_data: pair } });
  assert.equal(frappe.boot.app_data[0].app_logo_url.join(","), `${FORCEX_ERP},${FORCEX_ERP}`);
});

/* ---------- About / Support on the desktop avatar menu ------------------------------ */
const AVATAR_MENU = [{ label: "Edit Profile" }, { label: "About" }, { label: "Frappe Support" }, { label: "Logout" }];
const labels = (opts) => opts.options.map((o) => o.label).join(",");

test("About and Frappe Support are dropped from the desktop avatar menu", () => {
  const { frappe } = load(ON({ hide_desktop_menu: ["About", "Frappe Support"] }));
  new frappe.ui.Dropdown({ trigger: jq("desktop-avatar"), options: AVATAR_MENU });
  assert.equal(labels(FakeDropdown.built[0]), "Edit Profile,Logout");
});

test("other dropdowns keep every row", () => {
  const { frappe } = load(ON({ hide_desktop_menu: ["About"] }));
  new frappe.ui.Dropdown({ trigger: jq("some-other-menu"), options: AVATAR_MENU });
  assert.equal(labels(FakeDropdown.built[0]), "Edit Profile,About,Frappe Support,Logout");
});

test("the avatar menu is untouched when nothing is to be hidden", () => {
  const { frappe } = load(ON({ hide_desktop_menu: [] }));
  assert.equal(frappe.ui.Dropdown, FakeDropdown, "no wrapper installed");
});

test("the wrapped Dropdown is still a frappe.ui.Dropdown", () => {
  const { frappe } = load(ON({ hide_desktop_menu: ["About"] }));
  const dd = new frappe.ui.Dropdown({ trigger: jq("desktop-avatar"), options: [] });
  assert.ok(dd instanceof FakeDropdown);
});

test("hide_help survives a Desk build without SidebarHeader", () => {
  const document = makeDocument();
  const sandbox = { document, frappe: { boot: { forcex_theme: ON({ hide_help: true }) }, ui: {} }, console };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  assert.doesNotThrow(() => vm.runInContext(fs.readFileSync(BUNDLE, "utf8"), sandbox));
});
