"""The settings schema — every tab, section, field, label and default — and what is
derived from it (DEFAULTS, colour lists, the DocType fields, human labels).

To add a setting: add it to SECTIONS, run scripts/generate_theme_doctype.py, then use its
--fxh-* token in forcex_harbour.bundle.css. Tests fail until all three agree.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DOCTYPE = "ForceX Theme Settings"
ROLE_DOCTYPE = "ForceX Theme Role"
LOGIN_TITLE_MAX = 30


# A tiny description language for the settings page. Keeping it in code (not only in
# the DocType JSON) means defaults, labels and the CSS mapping are reviewed together.
@dataclass(frozen=True)
class F:
	"""One setting. kind: color | check | select | data | text | code | image | roles | button.

	A button stores nothing; it is a control on the form (handled in the form script)."""

	name: str
	kind: str
	label: str
	default: object = None
	dark: str | None = None  # color only: default of the "<name>_dark" twin
	options: tuple = ()
	length: int | None = None
	description: str | None = None
	depends_on: str | None = None
	mandatory_depends_on: str | None = None


@dataclass(frozen=True)
class Section:
	key: str
	label: str
	fields: tuple
	description: str | None = None
	depends_on: str | None = None

	@property
	def paired(self):
		"""Sections whose colours have light + dark twins render as two columns."""
		return all(f.kind == "color" and f.dark for f in self.fields)


@dataclass(frozen=True)
class Tab:
	key: str
	label: str
	sections: tuple = field(default_factory=tuple)


def color(name, label, light, dark=None, **kw):
	return F(name, "color", label, light, dark=dark, **kw)


def check(name, label, default=0, **kw):
	return F(name, "check", label, default, **kw)


def select(name, label, options, default, **kw):
	return F(name, "select", label, default, options=tuple(options), **kw)


APPEARANCE = {"Follow user preference": "auto", "Always Light": "light", "Always Dark": "dark"}
LOGIN_APPEARANCE = {"Light": "light", "Dark": "dark", "Follow device": "auto"}
RADIUS = {"Compact": "4px", "Default": "8px", "Rounded": "12px"}
FONTS = {
	# name: (CSS font stack, stylesheet to load or None when Frappe already ships it)
	"IBM Plex Sans": (
		"'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif",
		"https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600"
		"&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap",
	),
	"Inter": ("InterVariable, Inter, system-ui, -apple-system, 'Segoe UI', sans-serif", None),
	"System UI": ("system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif", None),
}

# Defaults come from ForceX_Service_Warranty_Prototype.html (navy #0F3870, deep #0B1C33,
# orange #F26522, CTA #C2410C, canvas #EEF1F6, ink #18222F, muted #4A5568, lines #DCE2EC).
# Dark values are the same family shifted to a "midnight harbour" canvas.
SECTIONS: tuple[Tab, ...] = (
	Tab(
		"general",
		"General",
		(
			Section(
				"theme",
				"Theme",
				(
					check(
						"enabled",
						"Enable ForceX theme",
						1,
						description="Untick to switch the theme off everywhere. No rebuild needed.",
					),
					select(
						"appearance",
						"Appearance",
						APPEARANCE,
						"Follow user preference",
						description="Always Light / Always Dark override each user's own Toggle Theme choice.",
					),
					select("font_family", "Font", FONTS, "IBM Plex Sans"),
					select(
						"corner_style",
						"Corner style",
						RADIUS,
						"Default",
						description="Roundness of buttons, inputs and cards.",
					),
				),
			),
			Section(
				"brand",
				"Brand colours",
				(
					color("primary_color", "Primary (brand navy)", "#0F3870"),
					color("accent_color", "Accent (highlights, active markers)", "#F26522"),
				),
				description="Used for accents across the Desk. Each area below has its own colours too.",
			),
		),
	),
	Tab(
		"login",
		"Login Page",
		(
			Section(
				"login_layout",
				"Layout & title",
				(
					F(
						"login_title",
						"data",
						"Login page title",
						"Sign in to ForceX",
						length=LOGIN_TITLE_MAX,
						description="Heading above the sign-in form (max 30 characters).",
					),
					select(
						"login_box_position",
						"Login box position",
						("Default", "Left", "Right"),
						"Default",
						description="Left / Right apply from 768px wide; phones always centre the box.",
					),
					select("login_appearance", "Login page appearance", LOGIN_APPEARANCE, "Light"),
					check("login_animation", "Fade-in animation", 1),
					check("show_login_accent", "Accent bar on the login box", 1),
					select(
						"login_footer",
						"Footer on login page",
						("Theme default", "Show", "Hide"),
						"Theme default",
					),
				),
			),
			Section(
				"login_bg",
				"Background",
				(
					select(
						"login_background",
						"Background",
						("Theme default", "Colour", "Image"),
						"Theme default",
					),
					color(
						"login_background_color",
						"Background colour",
						"#0B1C33",
						depends_on="eval:doc.login_background=='Colour'",
						mandatory_depends_on="eval:doc.login_background=='Colour'",
					),
					F(
						"login_background_image",
						"image",
						"Background image",
						None,
						depends_on="eval:doc.login_background=='Image'",
						mandatory_depends_on="eval:doc.login_background=='Image'",
						description="Attach as a public file, 1920px wide or more.",
					),
				),
			),
			Section(
				"login_colors",
				"Login colours",
				(
					color("login_page_bg", "Page background", "#EEF1F6", "#0B1C33"),
					color("login_card_bg", "Login box background", "#FFFFFF", "#121F31"),
					color("login_text", "Login box text", "#18222F", "#DCE4EE"),
					color("login_button_bg", "Login button", "#0F3870", "#F26522"),
					color("login_button_text", "Login button text", "#FFFFFF", "#0B1C33"),
					color("login_button_hover", "Login button hover", "#0B1C33", "#FF7A3D"),
				),
			),
			Section(
				"login_panel",
				"Side panel",
				(
					check("show_side_panel", "Show side panel", 0),
					F("side_panel_headline", "data", "Headline", "ForceX ERP", length=140),
					F(
						"side_panel_tagline",
						"text",
						"Tagline",
						"Service, warranty and operations on one secure platform.",
					),
				),
				description="Fills the empty half of the page when the login box is on the left or right.",
				depends_on="eval:doc.login_box_position!='Default'",
			),
		),
	),
	Tab(
		"navigation",
		"Navigation",
		(
			Section(
				"navbar",
				"Page header (navbar)",
				(
					color("navbar_bg", "Header background", "#FFFFFF", "#0E1A2B"),
					color("navbar_text", "Header text & icons", "#18222F", "#DCE4EE"),
				),
				description="In v16 the top bar is the page header with breadcrumbs and actions.",
			),
			Section(
				"sidebar",
				"Sidebar",
				(
					color("sidebar_bg", "Sidebar background", "#0B1C33", "#08111C"),
					color("sidebar_text", "Sidebar text & icons", "#C9D3E3", "#B3C0D0"),
					color("sidebar_active_bg", "Active item background", "#13284A", "#16304F"),
					color("sidebar_active_text", "Active item text", "#FFFFFF", "#FFFFFF"),
				),
			),
			Section(
				"nav_visibility",
				"Visibility",
				(
					check("hide_help", "Hide Help in the sidebar menu", 0),
					check(
						"hide_about",
						"Hide About",
						1,
						description="Removes 'About' from the Help menu and the desktop page's profile menu.",
					),
					check(
						"hide_support",
						"Hide Support",
						1,
						description="Removes the upstream support-site link from the same two menus.",
					),
					F(
						"hide_search_for_roles",
						"roles",
						"Hide search for these roles",
						[],
						description="Users with any of these roles get no search bar. Administrator is never hidden.",
					),
				),
			),
		),
	),
	Tab(
		"buttons",
		"Buttons",
		(
			Section(
				"primary_btn",
				"Primary buttons",
				(
					color("primary_btn_bg", "Background", "#0F3870", "#F26522"),
					color("primary_btn_text", "Text", "#FFFFFF", "#0B1C33"),
					color("primary_btn_hover", "Hover background", "#0B1C33", "#FF7A3D"),
				),
				description="Save, Submit, New and other solid buttons.",
			),
			Section(
				"secondary_btn",
				"Secondary buttons",
				(
					color("secondary_btn_bg", "Background", "#F1F4F9", "#1C2A3F"),
					color("secondary_btn_text", "Text", "#0F3870", "#DCE4EE"),
					color("secondary_btn_hover", "Hover background", "#E3E8F0", "#22324A"),
					color("secondary_btn_border", "Border", "#C9D2E0", "#33425A"),
				),
			),
		),
	),
	Tab(
		"body",
		"Body",
		(
			Section(
				"body_colors",
				"Page & content",
				(
					color("body_bg", "Page background", "#EEF1F6", "#0B1523"),
					color("content_bg", "Content box background", "#FFFFFF", "#121F31"),
					color("text_color", "Text", "#18222F", "#DCE4EE"),
					color("muted_text", "Muted text", "#4A5568", "#93A1B5"),
					color("border_color", "Borders", "#DCE2EC", "#22324A"),
				),
			),
			Section(
				"body_layout",
				"Layout",
				(
					check(
						"hide_list_sidebar",
						"Hide the list / form side panel",
						0,
						description="The left panel with Assigned To, Tags, Saved Filters.",
					),
				),
			),
		),
	),
	Tab(
		"tables",
		"Tables & Lists",
		(
			Section(
				"table_colors",
				"Table colours",
				(
					color("table_header_bg", "Header row background", "#F8FAFC", "#16243A"),
					color("table_header_text", "Header row text", "#4A5568", "#B3C0D0"),
					color("table_body_bg", "Row background", "#FFFFFF", "#121F31"),
					color("table_body_text", "Row text", "#18222F", "#DCE4EE"),
					color("table_row_hover", "Row hover", "#F7F9FC", "#182A42"),
				),
				description="List views, child tables in forms, and reports.",
			),
			Section(
				"list_behaviour",
				"List behaviour",
				(
					check("hide_list_likes_comments", "Hide likes & comment counts", 0),
					check("mobile_card_view", "Show list rows as cards on phones", 1),
					check("mobile_wrap_content", "Let row content wrap on phones", 1),
				),
			),
		),
	),
	Tab(
		"widgets",
		"Widgets & Inputs",
		(
			Section(
				"number_cards",
				"Number cards",
				(
					color("card_bg", "Background", "#FFFFFF", "#121F31"),
					color("card_border", "Border", "#DCE2EC", "#22324A"),
					color("card_value_text", "Value", "#0B1C33", "#F2F6FA"),
					color("card_label_text", "Label", "#4A5568", "#93A1B5"),
				),
			),
			Section(
				"inputs",
				"Form inputs",
				(
					color("input_bg", "Background", "#FFFFFF", "#0E1A2B"),
					color("input_border", "Border", "#C9D2E0", "#33425A"),
					color("input_text", "Text", "#18222F", "#DCE4EE"),
					color("input_label", "Label", "#4A5568", "#93A1B5"),
					color("input_focus", "Focus ring", "#F26522", "#FF7A3D"),
				),
			),
		),
	),
	Tab(
		"advanced",
		"Advanced",
		(
			Section(
				"transfer",
				"Export / Import",
				(
					F("export_settings_btn", "button", "Export settings"),
					F("import_settings_btn", "button", "Import settings"),
				),
				description="Export downloads this theme as a .json file. Import applies a file exported "
				"from any ForceX site; only the settings in the file change, and anything skipped is listed.",
			),
			Section(
				"custom",
				"Custom CSS",
				(
					F(
						"custom_css",
						"code",
						"Extra CSS",
						"",
						description="Added after the theme. Scope rules under html.fxh-on. '<' is not allowed.",
					),
				),
			),
		),
	),
)


def _all_fields():
	for tab in SECTIONS:
		for section in tab.sections:
			yield from section.fields


FIELDS: dict[str, F] = {f.name: f for f in _all_fields()}
PAIRED_COLORS: tuple[str, ...] = tuple(f.name for f in FIELDS.values() if f.kind == "color" and f.dark)
COLOR_FIELDS: tuple[str, ...] = tuple(
	n
	for f in FIELDS.values()
	if f.kind == "color"
	for n in ((f.name, f.name + "_dark") if f.dark else (f.name,))
)


def _defaults():
	d = {}
	for f in FIELDS.values():
		if f.kind == "button":
			continue  # buttons hold no value
		d[f.name] = list(f.default) if isinstance(f.default, list) else f.default
		if f.kind == "color" and f.dark:
			d[f.name + "_dark"] = f.dark
	return d


DEFAULTS: dict[str, object] = _defaults()

# Legacy values from the first ForceX Harbour settings page
_LEGACY_SELECT = {"login_box_position": {"Center": "Default"}}


# =====================================================================================
# DocType generation (used by scripts/generate_theme_doctype.py and the schema test)
# =====================================================================================
_FIELDTYPE = {
	"color": "Color",
	"check": "Check",
	"select": "Select",
	"data": "Data",
	"text": "Small Text",
	"code": "Code",
	"image": "Attach Image",
	"roles": "Table MultiSelect",
	"button": "Button",
}


def as_doctype_default(value):
	"""How a Python default is written in DocType JSON ("1", "#FFFFFF", or absent)."""
	if value is None or value == "" or isinstance(value, list):
		return None
	if isinstance(value, bool):
		value = int(value)
	return str(value)


def _field_dict(f: F, name=None, label=None, default=None):
	d = {"fieldname": name or f.name, "fieldtype": _FIELDTYPE[f.kind], "label": label or f.label}
	default = as_doctype_default(f.default if default is None else default)
	if default is not None:
		d["default"] = default
	if f.kind == "select":
		d["options"] = "\n".join(f.options)
	if f.kind == "roles":
		d["options"] = ROLE_DOCTYPE
	if f.kind == "code":
		d["options"] = "CSS"
	if f.length:
		d["length"] = f.length
	for key in ("description", "depends_on", "mandatory_depends_on"):
		if getattr(f, key):
			d[key] = getattr(f, key)
	return d


def doctype_fields() -> list[dict]:
	"""The exact `fields` list of the ForceX Theme Settings DocType."""
	out = []
	for tab in SECTIONS:
		out.append({"fieldname": f"{tab.key}_tab", "fieldtype": "Tab Break", "label": tab.label})
		for s in tab.sections:
			sec = {"fieldname": f"{s.key}_section", "fieldtype": "Section Break", "label": s.label}
			if s.description:
				sec["description"] = s.description
			if s.depends_on:
				sec["depends_on"] = s.depends_on
			out.append(sec)
			if s.paired:
				# Two columns: light values on the left, their dark twins on the right
				out.append(
					{"fieldname": f"{s.key}_light_col", "fieldtype": "Column Break", "label": "Light mode"}
				)
				out.extend(_field_dict(f) for f in s.fields)
				out.append(
					{"fieldname": f"{s.key}_dark_col", "fieldtype": "Column Break", "label": "Dark mode"}
				)
				out.extend(_field_dict(f, f.name + "_dark", f.label + " (dark)", f.dark) for f in s.fields)
			else:
				out.extend(_field_dict(f) for f in s.fields)
	return out


# =====================================================================================
# Human labels (form wording, used in validation and import messages)
# =====================================================================================
def _section_labels():
	return {f.name: sec.label for tab in SECTIONS for sec in tab.sections for f in sec.fields}


_SECTION_OF = _section_labels()
_LABEL_COUNT: dict[str, int] = {}
for _f in FIELDS.values():
	_LABEL_COUNT[_f.label] = _LABEL_COUNT.get(_f.label, 0) + 1


def label_of(name: str) -> str:
	"""Human label for a setting, as on the form: 'Header background (dark)'.
	Labels used in more than one section get the section first: 'Primary buttons > Background'."""
	dark = name.endswith("_dark") and name[:-5] in FIELDS
	base = name[:-5] if dark else name
	f = FIELDS.get(base)
	if not f:
		return name
	label = f.label if _LABEL_COUNT[f.label] == 1 else f"{_SECTION_OF[base]} > {f.label}"
	return label + (" (dark)" if dark else "")
