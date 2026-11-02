// Copyright (c) 2026, SAS Infosystem Pvt Ltd and contributors
// For license information, please see license.txt

// ForceX Theme Settings — form buttons.
//   Export                          downloads the whole theme as a .json file
//   Import                          applies a .json export (from this or another site)
//   Clear Cache                     clears Desk boot + website page caches, then reloads
//   Actions → Reset to defaults     puts every field back to the prefilled palette
//   Actions → Preview login page    opens /login in a new tab
// Export / Import also sit on the Advanced tab as buttons (export_settings_btn,
// import_settings_btn) so they are easy to find.
// The theme is applied when the Desk loads, so after any change we reload the page.

const FXH_API = "sas_forcex.theme";

frappe.ui.form.on("ForceX Theme Settings", {
	refresh(frm) {
		// top-level toolbar buttons
		frm.add_custom_button(__("Export"), () => fxhExport());
		frm.add_custom_button(__("Import"), () => fxhImport(frm));
		frm.add_custom_button(__("Clear Cache"), () => fxhClearCache());

		const actions = __("Actions");
		frm.add_custom_button(__("Reset to ForceX defaults"), () => fxhReset(), actions);
		frm.add_custom_button(__("Preview login page"), () => window.open("/login", "_blank"), actions);
	},

	// the same two actions as Button fields on the Advanced tab
	export_settings_btn() {
		fxhExport();
	},
	import_settings_btn(frm) {
		fxhImport(frm);
	},

	after_save() {
		frappe.show_alert({ message: __("Theme saved. Reloading to apply…"), indicator: "green" });
		fxhReload();
	},
});

/* ---------------------------------------------------------------- cache / reset */
function fxhClearCache() {
	frappe.xcall(`${FXH_API}.clear_theme_cache`).then((msg) => {
		frappe.show_alert({ message: msg, indicator: "green" });
		fxhReload();
	});
}

function fxhReset() {
	frappe.confirm(__("Every theme setting will go back to the ForceX defaults. Continue?"), () =>
		frappe.xcall(`${FXH_API}.reset_theme_settings`).then((msg) => {
			frappe.show_alert({ message: msg, indicator: "green" });
			fxhReload();
		})
	);
}

/* ---------------------------------------------------------------- export */
function fxhExport() {
	frappe.xcall(`${FXH_API}.export_theme_settings`).then((data) => {
		// file name: forcex-theme-<site>-<yyyy-mm-dd>.json
		const site = (data.site || "site").replace(/[^a-z0-9.-]/gi, "_");
		const day = (data.exported_on || frappe.datetime.now_datetime()).slice(0, 10);
		const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
		const link = document.createElement("a");
		link.href = URL.createObjectURL(blob);
		link.download = `forcex-theme-${site}-${day}.json`;
		document.body.appendChild(link);
		link.click();
		setTimeout(() => {
			URL.revokeObjectURL(link.href);
			link.remove();
		}, 500);
	});
}

/* ---------------------------------------------------------------- import */
// Three steps, each refusing early:
//   1. fxhImport          pick a file; cheap checks in the browser (type, empty, size)
//   2. fxhPreviewImport   server dry run → preview dialog (changes, skipped, warnings, errors)
//   3. fxhApplyImport     server validates again and saves; only reachable when the preview is ok
const FXH_IMPORT_MAX_BYTES = 200 * 1024; // same limit as theme_engine.IMPORT_MAX_BYTES

function fxhImport(frm) {
	if (frm.is_dirty()) {
		frappe.msgprint(__("Save or discard your changes before importing."));
		return;
	}
	// A plain file picker: the file is read in the browser and sent as text,
	// so nothing is uploaded to the File list.
	const input = document.createElement("input");
	input.type = "file";
	input.accept = ".json,application/json";
	input.onchange = () => {
		const file = input.files && input.files[0];
		if (!file) return;
		const problem = fxhCheckFile(file);
		if (problem) {
			frappe.msgprint({ title: __("Cannot import theme"), indicator: "red", message: problem });
			return;
		}
		const reader = new FileReader();
		reader.onload = () => fxhPreviewImport(file.name, String(reader.result || ""));
		reader.onerror = () => frappe.msgprint(__("Could not read {0}.", [frappe.utils.escape_html(file.name)]));
		reader.readAsText(file);
	};
	input.click();
}

/** Browser-side checks; returns an error message or null. The server checks everything again. */
function fxhCheckFile(file) {
	if (!/\.json$/i.test(file.name)) return __("Choose a .json file exported from ForceX Theme Settings.");
	if (file.size === 0) return __("The file is empty.");
	if (file.size > FXH_IMPORT_MAX_BYTES) return __("The file is too large to be a ForceX theme export.");
	return null;
}

function fxhPreviewImport(fileName, text) {
	frappe.xcall(`${FXH_API}.preview_theme_import`, { data: text }).then((report) => {
		const changes = report.changes || [];
		const canApply = report.ok && changes.length > 0;
		const dialog = new frappe.ui.Dialog({
			title: __("Import theme from {0}", [frappe.utils.escape_html(fileName)]),
			size: "large",
			fields: [{ fieldtype: "HTML", fieldname: "summary" }],
			primary_action_label: changes.length
				? __("Apply {0} changes", [changes.length])
				: __("Nothing to apply"),
			primary_action: () => {
				dialog.hide();
				fxhApplyImport(text);
			},
		});
		dialog.fields_dict.summary.$wrapper.html(fxhPreviewHtml(report));
		dialog.get_primary_btn().prop("disabled", !canApply);
		dialog.show();
	});
}

function fxhApplyImport(text) {
	frappe.xcall(`${FXH_API}.import_theme_settings`, { data: text }).then((result) => {
		frappe.show_alert({
			message: __("Imported {0} changes. Reloading…", [result.applied]),
			indicator: "green",
		});
		fxhReload();
	});
}

/** The preview as HTML. Every value from the file is escaped; swatches only for real hex colours. */
function fxhPreviewHtml(report) {
	const esc = frappe.utils.escape_html;
	const swatch = (value) =>
		/^#[0-9A-F]{6}$/i.test(value || "")
			? `<span style="display:inline-block;width:14px;height:14px;border-radius:3px;border:1px solid var(--border-color);background:${value};vertical-align:middle;margin-right:6px"></span>`
			: "";
	const show = (value, isColor) =>
		(isColor ? swatch(value) : "") + esc(Array.isArray(value) ? value.join(", ") : String(value ?? ""));
	const list = (items, indicator, title) =>
		items && items.length
			? `<div class="alert alert-${indicator}" style="margin-bottom:12px"><b>${title}</b><ul style="margin:6px 0 0;padding-left:18px">${items
					.map((i) => `<li>${esc(i)}</li>`)
					.join("")}</ul></div>`
			: "";

	const changes = report.changes || [];
	let html = list(report.errors, "danger", __("Cannot import — fix these first"));
	html += `<p>${__("{0} settings will change, {1} are already the same.", [changes.length, report.unchanged || 0])}</p>`;
	if (changes.length) {
		html += `<table class="table table-bordered table-sm"><thead><tr><th>${__("Setting")}</th><th>${__("Now")}</th><th>${__("After import")}</th></tr></thead><tbody>`;
		html += changes
			.map((c) => `<tr><td>${esc(c.label)}</td><td>${show(c.old, c.is_color)}</td><td>${show(c.new, c.is_color)}</td></tr>`)
			.join("");
		html += "</tbody></table>";
	}
	html += list(report.skipped, "warning", __("Left out (the rest is still imported)"));
	html += list(report.warnings, "info", __("Readability after import"));
	return html;
}

function fxhReload() {
	// small delay so the alert is seen before the reload
	setTimeout(() => window.location.reload(), 900);
}
