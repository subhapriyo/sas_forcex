"""Unit tests for sas_forcex.theme_engine — the pure (framework-free) theme logic.

These run anywhere, no bench or site needed:

    cd apps/sas_forcex
    python -m unittest discover -s sas_forcex/tests -t .

`bench --site <site> run-tests --app sas_forcex` picks them up as well.

TDD note: this file was written before theme_engine.py. Each block below states a
behaviour the settings page promises; the engine was written to make them pass.
"""

import json
import re
import unittest
from pathlib import Path

from sas_forcex import theme_engine as te

APP = Path(__file__).resolve().parents[1]
HARBOUR_CSS = APP / "public" / "css" / "forcex_harbour.bundle.css"

# Colour variables frappe_desk_theme (v1.1.0) sets on <html> and uses with !important.
FRAPPE_DESK_THEME_COLOUR_VARS = (
	"--body-bg", "--content-bg", "--content-text-color", "--page-heading-color",
	"--navbar-bg", "--navbar-color", "--sidebar-bg", "--sidebar-text-color",
	"--btn-primary-bg", "--btn-primary-color", "--btn-primary-hover-bg", "--btn-primary-hover-color",
	"--btn-secondary-bg", "--btn-secondary-color", "--btn-secondary-hover-bg", "--btn-secondary-hover-color",
	"--table-head-bg", "--table-head-color", "--table-body-bg", "--table-body-color",
	"--widget-bg", "--widget-border", "--widget-color",
	"--input-bg", "--input-border", "--input-color", "--input-label-color",
	"--login-box-bg", "--login-btn-bg", "--login-btn-color", "--login-btn-hover-bg", "--login-btn-hover-color",
)  # fmt: skip


# --------------------------------------------------------------------- colour maths
class TestColourMaths(unittest.TestCase):
	def test_normalize_hex_accepts_common_spellings(self):
		self.assertEqual(te.normalize_hex("#abc"), "#AABBCC")
		self.assertEqual(te.normalize_hex("0f3870"), "#0F3870")
		self.assertEqual(te.normalize_hex("  #0F3870 "), "#0F3870")

	def test_normalize_hex_rejects_anything_else(self):
		for bad in ("red", "#12345G", "#1234", "", None, "rgb(0,0,0)", "#0F3870;}body{"):
			self.assertIsNone(te.normalize_hex(bad), bad)
		self.assertEqual(te.normalize_hex("nope", "#FFFFFF"), "#FFFFFF")

	def test_contrast_extremes(self):
		self.assertAlmostEqual(te.contrast("#000000", "#FFFFFF"), 21.0, places=1)
		self.assertAlmostEqual(te.contrast("#0F3870", "#0F3870"), 1.0, places=5)

	def test_readable_on_picks_the_stronger_text(self):
		self.assertEqual(te.readable_on("#0F3870"), te.LIGHT_TEXT)
		self.assertEqual(te.readable_on("#FFFFFF"), te.DARK_TEXT)

	def test_hover_moves_away_from_the_extreme(self):
		self.assertGreater(te.luminance(te.hover_of("#0F3870")), te.luminance("#0F3870"))
		self.assertLess(te.luminance(te.hover_of("#FFFFFF")), te.luminance("#FFFFFF"))


# --------------------------------------------------------------------- schema & defaults
class TestDefaults(unittest.TestCase):
	def test_every_colour_default_is_valid_hex(self):
		for name in te.COLOR_FIELDS:
			self.assertEqual(te.normalize_hex(te.DEFAULTS[name]), te.DEFAULTS[name], name)

	def test_paired_colours_have_a_dark_twin(self):
		for key in te.PAIRED_COLORS:
			self.assertIn(key, te.DEFAULTS)
			self.assertIn(key + "_dark", te.DEFAULTS)

	def test_defaults_follow_the_forcex_prototype_palette(self):
		# Navy + orange from ForceX_Service_Warranty_Prototype.html
		self.assertEqual(te.DEFAULTS["primary_color"], "#0F3870")
		self.assertEqual(te.DEFAULTS["accent_color"], "#F26522")
		self.assertEqual(te.DEFAULTS["body_bg"], "#EEF1F6")
		self.assertEqual(te.DEFAULTS["font_family"], "IBM Plex Sans")

	def test_prefilled_theme_is_readable_in_both_modes(self):
		"""The out-of-the-box theme must pass every contrast check we warn about."""
		self.assertEqual(te.contrast_warnings(te.DEFAULTS), [])

	def test_login_title_default_fits_the_limit(self):
		self.assertLessEqual(len(te.DEFAULTS["login_title"]), te.LOGIN_TITLE_MAX)
		self.assertEqual(te.LOGIN_TITLE_MAX, 30)

	def test_fieldnames_are_unique(self):
		names = [f["fieldname"] for f in te.doctype_fields()]
		self.assertEqual(len(names), len(set(names)))


# --------------------------------------------------------------------- coercion
class TestCoerce(unittest.TestCase):
	def test_missing_and_empty_values_fall_back_to_defaults(self):
		s = te.coerce_settings({"primary_color": "", "body_bg": None})
		self.assertEqual(s["primary_color"], te.DEFAULTS["primary_color"])
		self.assertEqual(s["body_bg"], te.DEFAULTS["body_bg"])

	def test_bad_colour_falls_back_instead_of_reaching_css(self):
		s = te.coerce_settings({"navbar_bg": "#000;} body{display:none"})
		self.assertEqual(s["navbar_bg"], te.DEFAULTS["navbar_bg"])

	def test_checks_become_ints(self):
		s = te.coerce_settings({"hide_help": "1", "enabled": 0, "mobile_card_view": True})
		self.assertEqual((s["hide_help"], s["enabled"], s["mobile_card_view"]), (1, 0, 1))

	def test_unknown_select_value_falls_back(self):
		s = te.coerce_settings({"login_box_position": "Upside down"})
		self.assertEqual(s["login_box_position"], "Default")

	def test_legacy_center_position_maps_to_default(self):
		self.assertEqual(
			te.coerce_settings({"login_box_position": "Center"})["login_box_position"], "Default"
		)

	def test_login_title_is_trimmed_and_capped(self):
		s = te.coerce_settings({"login_title": "  " + "x" * 50 + "  "})
		self.assertEqual(s["login_title"], "x" * 30)

	def test_unknown_keys_are_dropped(self):
		self.assertNotIn("evil", te.coerce_settings({"evil": "1"}))

	def test_roles_accept_child_rows_or_plain_names(self):
		rows = [{"role": "Accounts User"}, {"role": ""}, "Sales User"]
		s = te.coerce_settings({"hide_search_for_roles": rows})
		self.assertEqual(s["hide_search_for_roles"], ["Accounts User", "Sales User"])


# --------------------------------------------------------------------- contrast warnings
class TestContrastWarnings(unittest.TestCase):
	def test_white_on_white_is_flagged(self):
		warnings = te.contrast_warnings({"primary_btn_bg": "#FFFFFF", "primary_btn_text": "#FFFFFF"})
		self.assertTrue(any("Primary button" in w for w in warnings), warnings)

	def test_dark_mode_pairs_are_checked_too(self):
		warnings = te.contrast_warnings({"text_color_dark": "#121F31"})
		self.assertTrue(any("dark" in w.lower() for w in warnings), warnings)


# --------------------------------------------------------------------- CSS output
class TestBuildCss(unittest.TestCase):
	def setUp(self):
		self.css = te.build_css(te.DEFAULTS)

	def test_has_one_block_per_mode(self):
		self.assertIn('html.fxh-on:not([data-theme="dark"]){', self.css)
		self.assertIn('html.fxh-on[data-theme="dark"]{', self.css)

	def test_light_and_dark_values_land_in_their_own_block(self):
		light, dark = self.css.split('html.fxh-on[data-theme="dark"]{', 1)
		self.assertIn("--fxh-primary-btn-bg:#0F3870", light)
		self.assertIn("--fxh-primary-btn-bg:" + te.DEFAULTS["primary_btn_bg_dark"], dark)

	def test_derived_tokens_exist(self):
		v = te.build_vars(te.DEFAULTS, "light")
		for name in ("--fxh-primary-btn-active", "--fxh-ring", "--fxh-radius", "--fxh-font"):
			self.assertIn(name, v)

	def test_every_var_the_stylesheet_reads_is_produced(self):
		"""Drift guard: forcex_harbour.bundle.css may only use --fxh-* tokens the engine emits
		(tokens used with a fallback, var(--x, y), are optional by design)."""
		css = HARBOUR_CSS.read_text(encoding="utf-8")
		used = set(re.findall(r"var\((--fxh-[a-z0-9-]+)\)", css))
		produced = set(te.build_vars(te.DEFAULTS, "light")) & set(te.build_vars(te.DEFAULTS, "dark"))
		self.assertEqual(sorted(used - produced), [])

	def test_stylesheet_ships_the_default_tokens(self):
		"""Regression: with only the stylesheet loaded (stale server, cached boot, failed
		script) every --fxh-* token was undefined, so --primary was empty and ticked
		checkboxes / primary buttons rendered blank. The bundle must carry the defaults."""
		css = HARBOUR_CSS.read_text(encoding="utf-8")
		block = re.search(r"/\* fxh:defaults:start.*?\*/\n(.*?)/\* fxh:defaults:end \*/", css, re.S)
		self.assertIsNotNone(block, "defaults block markers missing — run scripts/generate_theme_doctype.py")
		self.assertEqual(block.group(1), te.default_tokens_css())

	def test_saved_settings_outrank_the_shipped_defaults(self):
		"""Shipped defaults use .fxh-on (0,2,0); saved settings use html.fxh-on (0,2,1)."""
		self.assertTrue(te.default_tokens_css().startswith('.fxh-on:not([data-theme="dark"])'))
		self.assertTrue(te.build_css(te.DEFAULTS).startswith('html.fxh-on:not([data-theme="dark"])'))

	def test_frappe_desk_theme_colours_are_fed_forcex_tokens(self):
		"""Regression (sil-dev): frappe_desk_theme forces colours with !important through its own
		variables, set inline on <html>. Unless ForceX re-defines those variables lower down
		(on <body>), its dark sidebar text sat on the ForceX navy highlight and was unreadable."""
		css = HARBOUR_CSS.read_text(encoding="utf-8")
		block = re.search(
			r"/\* compat:frappe_desk_theme:start \*/(.*?)/\* compat:frappe_desk_theme:end \*/", css, re.S
		)
		self.assertIsNotNone(block, "frappe_desk_theme compatibility block missing")
		declared = dict(re.findall(r"(--[a-z0-9-]+):\s*var\((--fxh-[a-z0-9-]+)\)", block.group(1)))
		for name in FRAPPE_DESK_THEME_COLOUR_VARS:
			self.assertIn(name, declared, f"{name} is not fed a ForceX token")
		self.assertIn("html.fxh-on body", block.group(1))
		self.assertIn(".active-sidebar", block.group(1), "active row needs its own text colour")

	def test_custom_css_cannot_close_the_style_tag(self):
		css = te.build_css(dict(te.DEFAULTS, custom_css="a{color:red}</style><script>alert(1)</script>"))
		self.assertIn("a{color:red}", css)
		self.assertNotIn("<", css)


# --------------------------------------------------------------------- client config
class TestBuildConfig(unittest.TestCase):
	def test_disabled_theme_sends_nothing_to_style(self):
		cfg = te.build_config({"enabled": 0})
		self.assertEqual(cfg, {"enabled": 0, "classes": [], "css": ""})

	def test_desk_toggles_become_classes(self):
		cfg = te.build_config({"hide_list_sidebar": 1, "hide_list_likes_comments": 1, "mobile_card_view": 1})
		for cls in ("fxh-on", "fxh-hide-list-sidebar", "fxh-hide-likes", "fxh-mobile-cards"):
			self.assertIn(cls, cfg["classes"])

	def test_hide_help_is_a_flag_for_the_desk_script(self):
		self.assertTrue(te.build_config({"hide_help": 1})["hide_help"])
		self.assertFalse(te.build_config({"hide_help": 0})["hide_help"])

	def test_theme_icon_is_shown_by_default(self):
		self.assertEqual(te.DEFAULTS["show_theme_icon"], 1)

	def test_about_and_support_are_hidden_by_default(self):
		self.assertEqual((te.DEFAULTS["hide_about"], te.DEFAULTS["hide_support"]), (1, 1))
		cfg = te.build_config({})
		self.assertTrue(cfg["hide_about"] and cfg["hide_support"])
		# the desktop page's avatar menu is built in the browser, so it gets the labels to drop
		self.assertEqual(cfg["hide_desktop_menu"], ["About", "Frappe Support"])

	def test_about_and_support_can_be_kept(self):
		cfg = te.build_config({"hide_about": 0, "hide_support": 0})
		self.assertFalse(cfg["hide_about"] or cfg["hide_support"])
		self.assertEqual(cfg["hide_desktop_menu"], [])

	def test_search_is_hidden_only_for_listed_roles(self):
		raw = {"hide_search_for_roles": [{"role": "Accounts User"}]}
		hidden = te.build_config(raw, roles=["Employee", "Accounts User"])
		shown = te.build_config(raw, roles=["Employee"])
		self.assertTrue(hidden["hide_search"])
		self.assertIn("fxh-hide-search", hidden["classes"])
		self.assertFalse(shown["hide_search"])

	def test_appearance_mapping(self):
		self.assertEqual(te.build_config({})["appearance"], "auto")
		self.assertEqual(te.build_config({"appearance": "Always Dark"})["appearance"], "dark")
		self.assertEqual(te.build_config({"appearance": "Always Light"})["appearance"], "light")

	def test_font_url_only_for_webfonts_frappe_does_not_ship(self):
		self.assertIn("fonts.googleapis.com", te.build_config({"font_family": "IBM Plex Sans"})["font_url"])
		self.assertIsNone(te.build_config({"font_family": "Inter"})["font_url"])


class TestLoginConfig(unittest.TestCase):
	def test_position_and_animation_classes(self):
		cfg = te.build_config({"login_box_position": "Left", "login_animation": 1}, for_login=True)
		self.assertIn("fxh-login-left", cfg["classes"])
		self.assertIn("fxh-login-animate", cfg["classes"])

	def test_title_is_passed_through(self):
		cfg = te.build_config({"login_title": "Welcome to ForceX"}, for_login=True)
		self.assertEqual(cfg["login"]["title"], "Welcome to ForceX")

	def test_colour_background(self):
		cfg = te.build_config(
			{"login_background": "Colour", "login_background_color": "#112233"}, for_login=True
		)
		self.assertIn("fxh-login-bg-color", cfg["classes"])
		self.assertIn("--fxh-login-bg:#112233", cfg["css"])

	def test_unsafe_image_url_is_ignored(self):
		cfg = te.build_config(
			{"login_background": "Image", "login_background_image": "javascript:alert(1)"}, for_login=True
		)
		self.assertNotIn("fxh-login-bg-image", cfg["classes"])
		self.assertNotIn("javascript", cfg["css"])

	def test_safe_image_url_is_used(self):
		cfg = te.build_config(
			{"login_background": "Image", "login_background_image": "/files/harbour.jpg"}, for_login=True
		)
		self.assertIn("fxh-login-bg-image", cfg["classes"])
		self.assertIn('url("/files/harbour.jpg")', cfg["css"])

	def test_login_theme(self):
		self.assertEqual(
			te.build_config({"login_appearance": "Dark"}, for_login=True)["login"]["theme"], "dark"
		)
		self.assertEqual(te.build_config({}, for_login=True)["login"]["theme"], "light")

	def test_side_panel_only_when_box_is_on_a_side(self):
		raw = {"show_side_panel": 1, "side_panel_headline": "Hi"}
		self.assertNotIn(
			"panel", te.build_config(dict(raw, login_box_position="Default"), for_login=True)["login"]
		)
		self.assertIn(
			"panel", te.build_config(dict(raw, login_box_position="Right"), for_login=True)["login"]
		)

	def test_desk_config_carries_no_login_block(self):
		self.assertNotIn("login", te.build_config({}))


class TestHeadScript(unittest.TestCase):
	def test_disabled_theme_injects_nothing(self):
		self.assertEqual(te.render_head_script(te.build_config({"enabled": 0}, for_login=True)), "")

	def test_payload_cannot_break_out_of_the_script_tag(self):
		cfg = te.build_config({"login_title": "</script><b>"}, for_login=True)
		html = te.render_head_script(cfg)
		self.assertEqual(html.count("</script>"), 1, "only our own closing tag")
		payload = re.search(r"\}\)\((\{.*\})\);</script>", html, re.S).group(1)
		self.assertEqual(json.loads(payload.replace("<\\/", "</"))["login"]["title"], "</script><b>")

	def test_font_link_and_css_are_in_the_head(self):
		html = te.render_head_script(te.build_config({}, for_login=True))
		self.assertIn("fxh-theme-vars", html)
		self.assertIn("fonts.googleapis.com", html)


# --------------------------------------------------------------------- export / import
class TestExportImport(unittest.TestCase):
	def test_export_has_format_version_and_every_setting(self):
		data = te.export_payload(te.DEFAULTS, exported_on="2026-11-02 17:00", site="forcex.localhost")
		self.assertEqual((data["format"], data["version"]), (te.EXPORT_FORMAT, te.EXPORT_VERSION))
		self.assertEqual(set(data["settings"]), set(te.DEFAULTS))
		self.assertEqual(data["site"], "forcex.localhost")

	def test_export_then_import_round_trips(self):
		raw = dict(
			te.DEFAULTS, navbar_bg="#112233", hide_help=1, hide_search_for_roles=[{"role": "Accounts User"}]
		)
		values, skipped = te.parse_import(json.dumps(te.export_payload(raw)))
		self.assertEqual(skipped, [])
		self.assertEqual(values["navbar_bg"], "#112233")
		self.assertEqual(values["hide_help"], 1)
		self.assertEqual(values["hide_search_for_roles"], ["Accounts User"])

	def test_partial_file_only_touches_its_keys(self):
		values, _ = te.parse_import(
			json.dumps({"format": te.EXPORT_FORMAT, "version": 1, "settings": {"primary_btn_bg": "#abc"}})
		)
		self.assertEqual(values, {"primary_btn_bg": "#AABBCC"})

	def test_invalid_values_are_skipped_and_reported(self):
		settings = {
			"evil_key": 1,
			"navbar_bg": "red;}",
			"login_box_position": "Upside down",
			"login_title": "x" * 31,
			"custom_css": "</style>",
			"enabled": "maybe",
			"login_background_image": "javascript:alert(1)",
			"body_bg": "#FFFFFF",
		}
		values, skipped = te.parse_import(
			json.dumps({"format": te.EXPORT_FORMAT, "version": 1, "settings": settings})
		)
		self.assertEqual(values, {"body_bg": "#FFFFFF"})
		self.assertEqual(len(skipped), 7)
		self.assertTrue(any("evil_key" in s for s in skipped))

	def test_rejects_files_that_are_not_a_forcex_theme(self):
		for bad in (
			"not json",
			"[]",
			json.dumps({"settings": {}}),
			json.dumps({"format": "other", "version": 1, "settings": {}}),
			json.dumps({"format": te.EXPORT_FORMAT, "version": 1, "settings": []}),
		):
			with self.assertRaises(ValueError, msg=bad):
				te.parse_import(bad)

	def test_rejects_a_newer_format_version(self):
		with self.assertRaises(ValueError):
			te.parse_import(
				json.dumps({"format": te.EXPORT_FORMAT, "version": te.EXPORT_VERSION + 1, "settings": {}})
			)

	def test_rejects_oversized_files(self):
		with self.assertRaises(ValueError):
			te.parse_import(" " * (te.IMPORT_MAX_BYTES + 1))


# --------------------------------------------------------------------- import validation (dry run)
def _file(settings, **head):
	return json.dumps({"format": te.EXPORT_FORMAT, "version": 1, "settings": settings, **head})


class TestValidateImport(unittest.TestCase):
	def test_reports_changes_against_the_current_theme(self):
		report = te.validate_import(
			_file({"navbar_bg": "#112233", "body_bg": te.DEFAULTS["body_bg"]}), te.DEFAULTS
		)
		self.assertTrue(report["ok"])
		self.assertEqual(report["unchanged"], 1)
		self.assertEqual(len(report["changes"]), 1)
		change = report["changes"][0]
		self.assertEqual((change["field"], change["old"], change["new"]), ("navbar_bg", "#FFFFFF", "#112233"))
		self.assertEqual(change["label"], "Header background")
		self.assertTrue(change["is_color"])

	def test_every_setting_has_a_unique_label(self):
		"""Import messages and the preview name settings by label, so no two may read alike."""
		labels = [te.label_of(name) for name in te.DEFAULTS]
		self.assertEqual(
			len(labels), len(set(labels)), sorted(lbl for lbl in labels if labels.count(lbl) > 1)
		)
		self.assertEqual(te.label_of("primary_btn_bg"), "Primary buttons > Background")

	def test_dark_twins_get_a_readable_label(self):
		report = te.validate_import(_file({"navbar_bg_dark": "#000000"}), te.DEFAULTS)
		self.assertEqual(report["changes"][0]["label"], "Header background (dark)")

	def test_file_problems_are_errors_not_exceptions(self):
		for text in (
			"",
			"not json",
			_file({}),
			json.dumps({"format": te.EXPORT_FORMAT, "version": True, "settings": {"a": 1}}),
			json.dumps({"format": te.EXPORT_FORMAT, "version": 0, "settings": {"body_bg": "#FFFFFF"}}),
		):
			report = te.validate_import(text, te.DEFAULTS)
			self.assertFalse(report["ok"], text)
			self.assertTrue(report["errors"], text)

	def test_skipped_values_use_labels_and_reasons(self):
		report = te.validate_import(_file({"navbar_bg": "red", "nope": 1}), te.DEFAULTS)
		self.assertTrue(report["ok"], "skips alone do not block")
		self.assertIn("Header background: not a hex colour", report["skipped"])
		self.assertIn("nope: unknown setting", report["skipped"])

	def test_text_length_limits(self):
		report = te.validate_import(
			_file(
				{
					"side_panel_headline": "x" * 141,
					"side_panel_tagline": "y" * 1001,
					"custom_css": "a{}" * 7000,
				}
			),
			te.DEFAULTS,
		)
		self.assertEqual(len(report["skipped"]), 3)

	def test_image_background_needs_an_image_that_exists_here(self):
		text = _file({"login_background": "Image", "login_background_image": "/files/harbour.jpg"})
		missing = te.validate_import(text, te.DEFAULTS, existing_files=[])
		self.assertFalse(missing["ok"])
		self.assertTrue(any("harbour.jpg" in s for s in missing["skipped"]))
		self.assertTrue(any("Background image" in e for e in missing["errors"]))
		present = te.validate_import(text, te.DEFAULTS, existing_files=["/files/harbour.jpg"])
		self.assertTrue(present["ok"], present["errors"])

	def test_external_image_urls_are_not_looked_up(self):
		text = _file({"login_background": "Image", "login_background_image": "https://cdn.example.com/a.jpg"})
		self.assertTrue(te.validate_import(text, te.DEFAULTS, existing_files=[])["ok"])

	def test_cross_field_rules_run_on_the_merged_result(self):
		# switching to Image without supplying one, while the site has none either
		report = te.validate_import(
			_file({"login_background": "Image"}), dict(te.DEFAULTS, login_background_image="")
		)
		self.assertFalse(report["ok"])

	def test_roles_missing_on_this_site_are_skipped(self):
		text = _file({"hide_search_for_roles": ["Accounts User", "Ghost Role"]})
		report = te.validate_import(text, te.DEFAULTS, existing_roles=["Accounts User"])
		self.assertTrue(any("Ghost Role" in s for s in report["skipped"]))
		self.assertEqual(report["values"]["hide_search_for_roles"], ["Accounts User"])

	def test_readability_warnings_for_the_result(self):
		report = te.validate_import(_file({"primary_btn_text": te.DEFAULTS["primary_btn_bg"]}), te.DEFAULTS)
		self.assertTrue(report["ok"])
		self.assertTrue(any("Primary button" in w for w in report["warnings"]))

	def test_nothing_to_change_is_reported(self):
		report = te.validate_import(_file({"body_bg": te.DEFAULTS["body_bg"]}), te.DEFAULTS)
		self.assertTrue(report["ok"])
		self.assertEqual(report["changes"], [])


# --------------------------------------------------------------------- one rulebook for save and import
class TestValidateValue(unittest.TestCase):
	"""validate_value / cross_field_errors are shared by the settings form (controller.validate)
	and by import, so a value the form refuses can never arrive through a file, and vice versa."""

	def test_cleans_valid_values(self):
		self.assertEqual(te.validate_value("navbar_bg", "#abc"), "#AABBCC")
		self.assertEqual(te.validate_value("hide_help", "1"), 1)
		self.assertEqual(te.validate_value("login_box_position", "Center"), "Default")
		self.assertEqual(te.validate_value("login_title", "  Hi  "), "Hi")

	def test_refuses_with_a_reason(self):
		cases = {
			"navbar_bg": "red",
			"hide_help": "yes",
			"corner_style": "Pointy",
			"login_title": "x" * 31,
			"side_panel_headline": "x" * 141,
			"custom_css": "<b>",
			"login_background_image": "javascript:alert(1)",
		}
		for name, value in cases.items():
			with self.assertRaises(ValueError, msg=name):
				te.validate_value(name, value)

	def test_unknown_setting_is_refused(self):
		with self.assertRaises(KeyError):
			te.validate_value("nope", 1)

	def test_cross_field_rules(self):
		self.assertEqual(te.cross_field_errors(te.DEFAULTS), [])
		errors = te.cross_field_errors(dict(te.DEFAULTS, login_background="Image", login_background_image=""))
		self.assertEqual(len(errors), 1)
		self.assertIn("Background image", errors[0])


if __name__ == "__main__":
	unittest.main()
