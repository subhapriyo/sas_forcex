/**
 * Unit tests for public/js/forcex_ui.bundle.js — the generic ForceX component library.
 *
 * Run:  node --test sas_forcex/tests_js/*.test.cjs   (from apps/sas_forcex; Node 18+, no npm packages)
 *
 * The bundle expects the Desk's global `frappe` object. We load it into a sandbox
 * with a tiny fake `frappe` that offers only what the bundle touches, so these
 * tests check OUR code, not the framework.
 */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const PUBLIC = path.join(__dirname, "..", "public");
const BUNDLE = path.join(PUBLIC, "js", "forcex_ui.bundle.js");

/** Fresh sandbox with a fake Desk, then load the bundle. Returns { forcex, formHandlers, wrappers }. */
function loadBundle() {
  const formHandlers = {}; // doctype -> handlers registered with frappe.ui.form.on
  const wrappers = []; // every element passed to $() — lets tests see addClass calls
  const sandbox = {
    window: {},
    console,
    $: (el) => ({ addClass: (cls) => wrappers.push({ el, cls }) }),
    frappe: {
      provide(ns) { // mimics frappe.provide("a.b") → creates nested objects
        let o = sandbox;
        for (const part of ns.split(".")) o = o[part] = o[part] || {};
      },
      utils: {
        escape_html: (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
          .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;"),
      },
      ui: { form: { on: (dt, handlers) => { formHandlers[dt] = handlers; } } },
    },
  };
  sandbox.window = sandbox; // bundle code may read window.forcex
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(BUNDLE, "utf8"), sandbox);
  return { forcex: sandbox.forcex, formHandlers, wrappers };
}

/* ---------- escaping (security: review item B20) ---------------------------- */
test("pill escapes HTML in its text", () => {
  const { forcex } = loadBundle();
  assert.equal(forcex.ui.pill("<b>x</b>", "ok"), '<span class="fx-pill fx-p-ok">&lt;b&gt;x&lt;/b&gt;</span>');
});

test("pill escapes the tone so it cannot break out of the class attribute", () => {
  const { forcex } = loadBundle();
  assert.ok(!forcex.ui.pill("x", '"><script>').includes("<script>"));
});

test("gate escapes labels and marks open items", () => {
  const { forcex } = loadBundle();
  const html = forcex.ui.gate([["<script>", false]]);
  assert.ok(html.includes("&lt;script&gt;"));
  assert.ok(!html.includes("<script>"));
  assert.ok(html.includes(">!<"), "an open gate item shows the ! marker");
});

test("gate shows a tick for satisfied items", () => {
  const { forcex } = loadBundle();
  assert.ok(forcex.ui.gate([["Done", true]]).includes(">✓<"));
});

test("btn escapes label, data attributes and href", () => {
  const { forcex } = loadBundle();
  const html = forcex.ui.btn('<x>', { href: 'javascript:"', data: { id: '"><img>' } });
  assert.ok(!html.includes("<x>"));
  assert.ok(!html.includes('"><img>'));
});

test("btn renders a disabled button when asked", () => {
  const { forcex } = loadBundle();
  assert.ok(forcex.ui.btn("Save", { disabled: true }).includes(" disabled"));
});

// TDD: this test was written first and failed — ui.opt used to put `color` into the
// style attribute unescaped, so a value like '"><img src=x onerror=…>' became live HTML.
test("opt escapes the accent colour", () => {
  const { forcex } = loadBundle();
  const html = forcex.ui.opt({
    name: "a", value: "b", title: "T", sub: "S", checked: true, color: '"><img src=x onerror=alert(1)>',
  });
  assert.ok(!html.includes("<img"), "colour must not inject markup");
});

test("opt shows the lock reason and disables a locked option", () => {
  const { forcex } = loadBundle();
  const html = forcex.ui.opt({ name: "a", value: "b", title: "Repair", sub: "", locked: "Unit is irreparable" });
  assert.ok(html.includes("disabled"));
  assert.ok(html.includes("Locked: Unit is irreparable"));
});

/* ---------- empty state / table --------------------------------------------- */
test("empty state has no button unless the caller passes one", () => {
  const { forcex } = loadBundle();
  const html = forcex.ui.empty("Nothing here", "Try later");
  assert.ok(!html.includes("<button"));
  assert.ok(html.includes("Nothing here"));
});

test("table shows an empty message when there are no rows", () => {
  const { forcex } = loadBundle();
  const html = forcex.ui.table([{ label: "Name", html: (r) => forcex.ui.e(r.name) }], []);
  assert.ok(html.includes("No records match this filter."));
});

/* ---------- generic form theming ----------------------------------------------- */
test("themeForms adds .fx-form and calls the app's hook on refresh", () => {
  const { forcex, formHandlers, wrappers } = loadBundle();
  const calls = [];
  forcex.ui.themeForms(["Demo DocType"], (frm, doctype) => calls.push(doctype));
  const frm = { wrapper: { id: "w1" } };
  formHandlers["Demo DocType"].refresh(frm);
  assert.deepEqual(wrappers, [{ el: frm.wrapper, cls: "fx-form" }]);
  assert.deepEqual(calls, ["Demo DocType"]);
});

test("themeForms works without a hook", () => {
  const { forcex, formHandlers } = loadBundle();
  forcex.ui.themeForms(["Demo DocType"]);
  assert.doesNotThrow(() => formHandlers["Demo DocType"].refresh({ wrapper: {} }));
});

/* ---------- this app stays generic --------------------------------------------- */
test("the platform UI kit contains nothing FLEETO-specific", () => {
  const src = fs.readFileSync(BUNDLE, "utf8");
  for (const word of ["Service Ticket", "STAGES", "Supplier RMA", "forcex-service"]) {
    assert.ok(!src.includes(word), `found FLEETO-specific "${word}" in forcex_ui.bundle.js`);
  }
});

test("component CSS no longer targets the removed cockpit page route", () => {
  const css = fs.readFileSync(path.join(PUBLIC, "css", "forcex_components.bundle.css"), "utf8");
  assert.ok(!css.includes("forcex-service"), "dead rule for the removed forcex-service page");
});
