"""ForceX theme engine — the public face of sas_forcex/forcex_theme/.

Everything the theme decides lives in that package (one file per concern, see its
__init__). Import from here — `from sas_forcex import theme_engine as engine` — so the
package can be reorganised without touching hooks, the controller, the patch, the
generator script or the tests.
"""

from sas_forcex.forcex_theme.branding import (
	APP_LOGOS,
	FORCEX_ERP_LOGO,
	THEME_SETTINGS_ICON,
	brand_app_data,
	desktop_menu_labels_to_hide,
	hide_help_items,
	rebrand_url,
)
from sas_forcex.forcex_theme.client import build_config, render_head_script
from sas_forcex.forcex_theme.colours import (
	DARK_TEXT,
	LIGHT_TEXT,
	contrast,
	hover_of,
	luminance,
	mix,
	normalize_hex,
	readable_on,
)
from sas_forcex.forcex_theme.css import build_css, build_vars, default_tokens_css, sanitize_custom_css
from sas_forcex.forcex_theme.rules import (
	CONTRAST_PAIRS,
	MIN_CONTRAST,
	TEXT_MAX,
	coerce_settings,
	contrast_warnings,
	cross_field_errors,
	validate_value,
)
from sas_forcex.forcex_theme.schema import (
	APPEARANCE,
	COLOR_FIELDS,
	DEFAULTS,
	DOCTYPE,
	FIELDS,
	FONTS,
	LOGIN_APPEARANCE,
	LOGIN_TITLE_MAX,
	PAIRED_COLORS,
	RADIUS,
	ROLE_DOCTYPE,
	SECTIONS,
	as_doctype_default,
	doctype_fields,
	label_of,
)
from sas_forcex.forcex_theme.transfer import (
	EXPORT_FORMAT,
	EXPORT_VERSION,
	IMPORT_MAX_BYTES,
	export_payload,
	parse_import,
	validate_import,
)
