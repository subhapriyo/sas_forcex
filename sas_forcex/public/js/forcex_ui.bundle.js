/* =============================================================================
   forcex_ui.bundle.js — ForceX component library (loaded on EVERY Desk page)
   ---------------------------------------------------------------------------
   Generic building blocks any ForceX app can use (pills, buttons, checklists,
   tables, option cards …). Nothing in here knows about FLEETO or any other
   product — product apps (e.g. sas_forcex_fleeto) build on top of forcex.ui.

   Rules for this file:
     • Every helper returns an HTML string and ESCAPES all data it is given.
       Parameters named *Html are the only exception: they are trusted markup
       the caller built (usually with other forcex.ui helpers).
     • Class names: first class gets the fx- prefix, modifiers stay plain
       (fx-btn sm pri) — see forcex_components.bundle.css.
     • Loaded via hooks.py → app_include_js on every Desk page, so keep it small.

   Tests: tests_js/forcex_ui.test.cjs   (run: node --test sas_forcex/tests_js/*.test.cjs)
   ============================================================================= */
(function () {
  "use strict";
  frappe.provide("forcex.ui");

  const ui = forcex.ui;

  /* ---------- Core helpers ---------------------------------------------------- */
  /** Translate a UI string when the Desk translator is present (it isn't in tests). */
  const t = (s) => (typeof __ === "function" ? __(s) : s);

  /** Escape any value for safe use in HTML text or attributes. null/undefined → "". */
  const e = (s) => {
    const text = s == null ? "" : String(s);
    if (frappe.utils && frappe.utils.escape_html) return frappe.utils.escape_html(text);
    return text.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  };

  ui.t = t;
  ui.e = e;

  /* ---------- Atoms --------------------------------------------------------- */
  /** Status pill. tone ∈ ok | bad | warn | info | mute | pur | or */
  ui.pill = (text, tone = "mute") => `<span class="fx-pill fx-p-${e(tone)}">${e(text)}</span>`;

  /** Priority pill: High → red, Medium → amber, anything else → grey. */
  ui.prioPill = (p) => ui.pill(t(p), p === "High" ? "bad" : p === "Medium" ? "warn" : "mute");

  /** Warranty pill: green when active, red when expired. */
  ui.warrantyPill = (active, label) => ui.pill(label, active ? "ok" : "bad");

  /** Button or link. kind: "" | "pri" | "cta" | "ghost"; size: "" | "sm"; act → data-fx-act. */
  ui.btn = (label, { kind = "", size = "", act = "", data = {}, disabled = false, href = "" } = {}) => {
    const attrs = Object.entries(data).map(([k, v]) => ` data-${e(k)}="${e(v)}"`).join("");
    const cls = ["fx-btn", kind, size].filter(Boolean).map(e).join(" ");
    const action = act ? ` data-fx-act="${e(act)}"` : "";
    return href
      ? `<a class="${cls}" href="${e(href)}"${action}${attrs}>${e(label)}</a>`
      : `<button class="${cls}"${action}${attrs}${disabled ? " disabled" : ""}>${e(label)}</button>`;
  };

  /** Page heading: eyebrow code + title + optional right-side markup (trusted). */
  ui.head = (code, title, rightHtml = "") =>
    `<div class="fx-row" style="align-items:flex-end;gap:16px"><div style="flex-grow:1">
       <div class="fx-eyebrow">${e(code)}</div><h1>${e(title)}</h1></div>${rightHtml}</div>`;

  /** Coloured note box. bodyHtml is trusted markup. tone ∈ ok | bad | warn | info | pur */
  ui.note = (bodyHtml, tone = "info") => `<div class="fx-note fx-n-${e(tone)}">${bodyHtml}</div>`;

  /** Empty state. actionHtml (optional, trusted) — e.g. a ui.btn(...) shown below the text. */
  ui.empty = (title, text, actionHtml = "") =>
    `<div class="fx-card fx-empty"><div style="font-weight:600;font-size:16px;color:var(--fx-ink)">${e(title)}</div>
       <div style="margin-top:6px">${e(text)}</div>
       ${actionHtml ? `<div style="margin-top:14px">${actionHtml}</div>` : ""}</div>`;

  /** Read-only field: label above a value box. */
  ui.ro = (label, value, mono = false) =>
    `<div><span class="fx-lbl">${e(label)}</span><div class="fx-in fx-ro ${mono ? "fx-mono" : ""}">${e(value)}</div></div>`;

  /* ---------- Molecules ----------------------------------------------------- */
  /** Gate checklist — items: [[label, ok], …]. Mirrors the server's GateItem list. */
  ui.gate = (items) => `<ul class="fx-gate">${items.map(([label, ok]) =>
    `<li><span class="fx-m" style="background:${ok ? "#1F7A45" : "#C2410C"}">${ok ? "✓" : "!"}</span>
         <span style="color:${ok ? "var(--fx-ink-2)" : "#9A3412"}">${e(label)}</span></li>`).join("")}</ul>`;

  /** KPI tiles — list: [[label, value, note], …] */
  ui.kpis = (list) => `<div class="fx-g6">${list.map(([l, v, n]) =>
    `<div class="fx-card fx-kpi"><div class="fx-small" style="color:var(--fx-mut);font-weight:500">${e(l)}</div>
       <div class="fx-v">${e(v)}</div><div class="fx-small">${e(n)}</div></div>`).join("")}</div>`;

  /** Clickable stage cards — list: [[code, name, count, word, value], …]; click fires data-fx-act=act. */
  ui.stageCards = (list, act = "stage") => `<div class="fx-g6">${list.map(([k, n, c, w, value]) =>
    `<a class="fx-stage" href="#" data-fx-act="${e(act)}" data-val="${e(value)}">
       <div class="fx-mono" style="font-size:11px;color:var(--fx-cta);font-weight:600">${e(k)}</div>
       <div style="font-weight:600;margin-top:4px">${e(n)}</div>
       <div class="fx-small" style="margin-top:6px">${e(c)} ${e(w)}</div></a>`).join("")}</div>`;

  /** Filter tabs — list: [[key, label, count], …] */
  ui.tabs = (list, active, act = "filter") => `<div class="fx-row" role="group" style="gap:6px">${list.map(([k, l, n]) =>
    `<button class="fx-tab ${k === active ? "on" : ""}" aria-pressed="${k === active}" data-fx-act="${e(act)}" data-val="${e(k)}">${e(l)} (${e(n)})</button>`).join("")}</div>`;

  /** Decision option card (radio). locked = reason string → disabled; color = accent when checked. */
  ui.opt = ({ name, value, title, sub, checked, locked, color }) => {
    // color is escaped too: it ends up inside a style attribute, so it must never carry markup.
    const accent = color ? e(color) : "";
    const ring = checked && accent ? ` style="border-color:${accent};box-shadow:inset 3px 0 0 ${accent}"` : "";
    return `<label class="fx-opt ${locked ? "off" : checked ? "on" : ""}"${ring}>
       <input type="radio" name="${e(name)}" value="${e(value)}" ${checked ? "checked" : ""} ${locked ? "disabled" : ""}>
       <span><span style="display:block;font-weight:700;font-size:13.5px${accent ? ";color:" + accent : ""}">${e(title)}</span>
       <span class="fx-small" style="display:block;margin-top:2px;color:${locked ? "#A61B1B" : "var(--fx-mut)"}">${e(locked ? t("Locked: ") + locked : sub)}</span></span></label>`;
  };

  /** Segmented control (e.g. REPAIRABLE / IRREPARABLE) — opts: [[value, label, tone g|r], …] */
  ui.segmented = (opts, current, act) => `<div role="group" style="display:flex">${opts.map(([v, l, tone]) =>
    `<button class="fx-seg ${v === current ? e(tone) : ""}" aria-pressed="${v === current}" data-fx-act="${e(act)}" data-val="${e(v)}">${e(l)}</button>`).join("")}</div>`;

  /** 1–5 star rating. */
  ui.stars = (value, act) => `<div class="fx-row" role="group" style="gap:6px">${[1, 2, 3, 4, 5].map((n) =>
    `<button class="fx-star ${n <= value ? "on" : ""}" aria-label="${n} ${e(t("star"))}" data-fx-act="${e(act)}" data-val="${n}">★</button>`).join("")}
    <span class="fx-mono" style="margin-left:6px;font-weight:600">${e(value || 0)} / 5</span></div>`;

  /** Step progress — labels[], done = number of finished steps. */
  ui.steps = (labels, done) => `<ol class="fx-steps">${labels.map((l, i) =>
    `<li style="color:${i < done ? "var(--fx-navy)" : i === done ? "#9A3412" : "var(--fx-mut2)"}">
       <i style="background:${i < done ? "var(--fx-navy)" : i === done ? "#F26522" : "var(--fx-line)"}"></i>${i + 1}. ${e(l)}</li>`).join("")}</ol>`;

  /** Timeline / logistics trail — items: [{at, text}] */
  ui.trail = (items) => `<ol class="fx-trail">${items.map((x) =>
    `<li class="on"><div class="fx-small fx-mono">${e(x.at)}</div><div style="font-size:13px">${e(x.text)}</div></li>`).join("")}</ol>`;

  /** Data table — cols: [{label, html(row), right}]; each html(row) must escape its own data via ui.e. */
  ui.table = (cols, rows, minWidth = 900) => `<div class="fx-scroll"><table class="fx-t" style="min-width:${Number(minWidth) || 900}px">
      <thead><tr>${cols.map((c) => `<th${c.right ? ' style="text-align:right"' : ""}>${e(c.label)}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr>${cols.map((c) => `<td${c.right ? ' style="text-align:right;white-space:nowrap"' : ""}>${c.html(r)}</td>`).join("")}</tr>`).join("")}</tbody>
    </table>${rows.length ? "" : `<div class="fx-empty">${t("No records match this filter.")}</div>`}</div>`;

  /* ---------- Form theming ---------------------------------------------------- */
  /**
   * Give standard Desk forms the ForceX look.
   *   forcex.ui.themeForms(["My DocType", …], (frm, doctype) => { …extra per-app work… })
   * Adds the .fx-form class (scope for forcex_components.bundle.css) on every refresh,
   * then calls onRefresh so a product app can add its own band, indicator, etc.
   */
  ui.themeForms = (doctypes, onRefresh) => {
    doctypes.forEach((doctype) => frappe.ui.form.on(doctype, {
      refresh(frm) {
        $(frm.wrapper).addClass("fx-form");
        if (typeof onRefresh === "function") onRefresh(frm, doctype);
      },
    }));
  };
})();
