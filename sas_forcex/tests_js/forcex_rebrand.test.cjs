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
function loadRebrand() {
  const listeners = [];
  const sandbox = {
    module: { exports: {} },
    document: { readyState: "loading", addEventListener: (type, fn) => listeners.push(type) },
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(BUNDLE, "utf8"), sandbox);
  return { rebrandText: sandbox.module.exports.rebrandText, forcex: sandbox.forcex, listeners };
}

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

/* ---------- boot behaviour ------------------------------------------------------- */
test("exposes forcex.rebrand and waits for the page before touching the DOM", () => {
  const { forcex, listeners } = loadRebrand();
  assert.equal(typeof forcex.rebrand, "function");
  assert.ok(forcex.rebrandLoaded);
  assert.deepEqual(listeners, ["DOMContentLoaded"]);
});
