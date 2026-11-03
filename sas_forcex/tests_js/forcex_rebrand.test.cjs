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
    ...globals,
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(BUNDLE, "utf8"), sandbox);
  const { rebrandText, isSkipped } = sandbox.module.exports;
  return { rebrandText, isSkipped, forcex: sandbox.forcex, listeners, sandbox };
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

/* ---------- boot behaviour ------------------------------------------------------- */
test("exposes forcex.rebrand and waits for the page before touching the DOM", () => {
  const { forcex, listeners } = loadRebrand();
  assert.equal(typeof forcex.rebrand, "function");
  assert.ok(forcex.rebrandLoaded);
  assert.deepEqual(listeners, ["DOMContentLoaded"]);
});
