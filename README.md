### ForceX (sas_forcex)

The ForceX platform layer, installed on every tenant:

| Path | What it is |
| --- | --- |
| `sas_forcex/theme_engine.py` | ForceX theme logic: settings schema, defaults, colour maths, CSS, login options (no Frappe import) |
| `sas_forcex/theme.py` | Frappe glue: boot / website hooks, **Clear Cache** and **Reset** endpoints, prefill |
| `ForceX Theme Settings` (DocType) | Light + dark theme settings page, generated from the engine schema |
| `public/css/forcex_harbour.bundle.css` | Maps the `--fxh-*` theme tokens onto Frappe v16 tokens and selectors |
| `public/js/forcex_harbour.bundle.js` | Applies the theme on Desk load (classes, tokens, forced light/dark, Help row) |
| `scripts/generate_theme_doctype.py` | Regenerates the settings DocType JSON from the engine schema |
| `public/css/forcex_desk_theme.bundle.css` | Legacy palette, no longer loaded |
| `public/css/forcex_components.bundle.css` | `.fx-*` design system used by the `forcex.ui` helpers |
| `public/js/forcex_rebrand.bundle.js` | Replaces Frappe / ERPNext / HRMS names with ForceX names in the UI |
| `public/js/forcex_ui.bundle.js` | Generic `forcex.ui` component kit + `themeForms()` |
| `tests_js/` | Node unit tests for both JS bundles |

Product features live in their own apps, e.g. **sas_forcex_fleeto** (FLEETO Service & Warranty).

### ForceX Theme

Open **ForceX Theme Settings** (System Manager). Tabs: General · Login Page · Navigation ·
Buttons · Body · Tables & Lists · Widgets & Inputs · Advanced. Every colour has a light and a
dark value, all prefilled with the ForceX palette (navy `#0F3870`, orange `#F26522`).
Buttons on the form: **Clear Cache**, **Actions → Reset to ForceX defaults**, **Actions → Preview login page**.
Saving warns (never blocks) when a colour pair falls below WCAG AA contrast.

Adding a setting: edit `SECTIONS` in `theme_engine.py` → `python scripts/generate_theme_doctype.py`
→ use the new `--fxh-*` token in `forcex_harbour.bundle.css` → `bench migrate`. The schema tests
fail if the DocType JSON or the stylesheet drift from the engine.

### Testing

```bash
# from apps/sas_forcex — no site needed
python -m unittest discover -s sas_forcex/tests -t .     # theme engine + DocType schema
node --test sas_forcex/tests_js/*.test.cjs                # Desk JS bundles

# needs a site
bench --site forcex.localhost run-tests --module sas_forcex.sas_forcex.doctype.forcex_theme_settings.test_forcex_theme_settings
```

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16
bench install-app sas_forcex
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/sas_forcex
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
