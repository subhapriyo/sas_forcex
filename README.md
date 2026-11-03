# ForceX (sas_forcex)

The ForceX platform layer for ERPNext / Frappe **v16**, installed on every ForceX tenant.
It brands the Desk and login page, adds the configurable **ForceX Harbour** theme (light + dark),
and ships a small UI kit used by the ForceX product apps.

Product features live in their own apps, e.g. **sas_forcex_fleeto** (FLEETO Service & Warranty).

## Contents

| Path | What it is |
| --- | --- |
| `sas_forcex/forcex_theme/` | Theme logic, one file per concern — no Frappe import, testable without a site |
| &nbsp;&nbsp;`colours.py` | Hex parsing, mixing, luminance, WCAG contrast, readable text colour |
| &nbsp;&nbsp;`schema.py` | Every setting: tabs, sections, fields, ForceX defaults, labels |
| &nbsp;&nbsp;`rules.py` | The single rulebook: value checks, cross-field rules, contrast warnings |
| &nbsp;&nbsp;`css.py` | Settings → `--fxh-*` CSS variables; custom CSS sanitising |
| &nbsp;&nbsp;`branding.py` | ForceX logos for upstream apps (ERPNext → ForceX ERP); which Help rows are About / Support |
| &nbsp;&nbsp;`client.py` | Config sent to the browser (Desk boot and login page) |
| &nbsp;&nbsp;`transfer.py` | Export file format and import validation |
| `sas_forcex/theme_engine.py` | Public facade over `forcex_theme/` — import from here |
| `sas_forcex/theme.py` | Frappe glue: boot / website hooks, Clear Cache, Reset, Prefill, Export, Import |
| `ForceX Theme Settings` (DocType) | The settings page, generated from `schema.py` |
| `ForceX Theme Role` (DocType) | Child table: roles that have the search bar hidden |
| `public/css/forcex_harbour.bundle.css` | Maps the `--fxh-*` tokens onto Frappe v16 tokens and selectors |
| `public/js/forcex_harbour.bundle.js` | Applies the theme and brand on Desk load (classes, tokens, light/dark, Help row, app logos, avatar menu) |
| `public/images/` | ForceX app logos (`forcex-*-logo.svg`) and the ForceX Theme apps-screen icon |
| `public/css/forcex_components.bundle.css` | `.fx-*` design system used by the `forcex.ui` helpers |
| `public/js/forcex_ui.bundle.js` | Generic `forcex.ui` component kit + `themeForms()` |
| `public/js/forcex_rebrand.bundle.js` | Replaces Frappe / ERPNext / HRMS names with ForceX names in the UI |
| `public/css/forcex_desk_theme.bundle.css` | Legacy palette, no longer loaded |
| `patches/v16_0/prefill_forcex_theme_settings.py` | Fills the settings with ForceX defaults and migrates old values |
| `patches/v16_0/hide_about_and_support.py`, `show_theme_icon.py` | Switch on new default-on options on existing sites |
| `patches/v16_0/rebrand_brand_settings.py` | Writes "ForceX" into the brand settings on existing sites |
| `scripts/generate_theme_doctype.py` | Regenerates the DocType JSON and the default tokens in the stylesheet |
| `sas_forcex/tests/`, `tests_js/` | Python and Node unit tests |

## ForceX Theme

Open **ForceX Theme Settings** (`/app/forcex-theme-settings`, System Manager only).

| Tab | What you can change |
| --- | --- |
| General | Enable / disable, appearance (follow user, always light, always dark), font, corner style, brand primary and accent colours |
| Login Page | Title (max 30 chars), box position (Default / Left / Right), light or dark login, fade-in animation, accent bar, footer, background colour or image, box and button colours, optional side panel |
| Navigation | Page header and sidebar colours (text and icons follow them), active item, show the ForceX Theme icon, hide Help, hide About, hide Support, hide search for selected roles |
| Buttons | Primary and secondary: background, text, hover (and border for secondary) |
| Body | Page and content backgrounds, text, muted text, borders, hide the list / form side panel |
| Tables & Lists | Header row, rows, row hover, hide likes & comment counts, cards and wrapping on phones |
| Widgets & Inputs | Number cards (background, border, value, label), input fields (background, border, text, label, focus ring) |
| Advanced | Export / Import settings, custom CSS |

Every colour has a light and a dark value, prefilled with the ForceX palette
(navy `#0F3870`, orange `#F26522`). Saving checks every value and lists all problems at once;
colour pairs below WCAG AA contrast (4.5:1) give a warning but still save.

Form buttons: **Clear Cache**, **Export**, **Import**, **Actions → Reset to ForceX defaults**,
**Actions → Preview login page**.

### Branding

- **ForceX app logos** — the upstream apps used on our sites get a ForceX logo in one
  family (100x100 tile, white glyph, ForceX accent; files in `public/images/`): ERP, HR,
  India Compliance, Framework and Helpdesk. They show on the apps screen, in the app
  switcher and on the dock; pages that draw an upstream logo themselves (e.g. the HR
  Roster) get it swapped in the browser. The ERP mark is also the Desk splash and website
  favicon, unless Website Settings sets its own. Other apps, and our own, keep their logos.
- **ForceX Theme icon** — a ForceX Theme tile on the apps screen opens ForceX Theme
  Settings. Administrator always sees it; other System Managers while *Navigation → Show
  ForceX Theme icon* is on (default). Hiding it doesn't change who may open the settings.
- **About / Support** — *Hide About* and *Hide Support* (on by default) remove About and
  Frappe Support from the Help menu and the desktop page's profile menu.
- **Names on screen** — `forcex_rebrand.bundle.js` turns Frappe / ERPNext / HRMS into
  ForceX names in the browser, including the Desk's own menu lists (Workspace, Module
  Def, ...). Business records are never rewritten. HRMS's standalone pages (`/hr/roster`,
  `/hrms`) bring their own HTML, so an `after_request` hook adds the script to them.
- **Names the server sends** — emails, browser tab titles, authenticator apps, the OAuth
  consent screen and the website footer read a few settings, listed in `BRAND_SETTINGS`
  (`forcex_theme/branding.py`). A patch and the install hook write "ForceX" into them,
  but only while they still hold the upstream default; a name a site chose is kept.
  Values code compares (e.g. "Frappe Mail", DocType names) are never renamed, and
  Frappe's / ERPNext's own files are never edited (`bench update` would undo it).
- **Upstream videos** — onboarding YouTube videos, YouTube/Vimeo players and thumbnails,
  ERPNext's video images and Frappe's help video dialog are hidden.

To brand another app's logo: put the SVG in `public/images/`, add the app to `APP_LOGOS`
and its upstream logo file(s) to `UPSTREAM_LOGOS` in `forcex_theme/branding.py`. The tests
check every file exists, is valid SVG and has a title.

### Export / Import

**Export** downloads the current settings as a `.json` file. **Import** shows a preview first —
every change with old and new value, anything skipped, warnings and errors — and nothing is saved
until you click **Apply**. The server checks the file again on Apply with the same rules as the
form: format and version, size (≤ 200 KB), every value, roles and files that must exist on this site.
A file with errors is never applied.

### Adding a setting

1. Add the field to `SECTIONS` in `sas_forcex/forcex_theme/schema.py` (and a rule in `rules.py` if needed).
2. Run `python scripts/generate_theme_doctype.py`.
3. Use the new `--fxh-*` token in `public/css/forcex_harbour.bundle.css`.
4. `bench --site <site> migrate` and `bench build --app sas_forcex`.

The schema tests fail if the DocType JSON or the stylesheet drift from `schema.py`.

### Works alongside frappe_desk_theme

If `frappe_desk_theme` is installed, ForceX redefines its variables so the ForceX colours win.
You don't need both; uninstalling `frappe_desk_theme` is recommended.

## Installation

```bash
cd ~/frappe-bench
bench get-app https://github.com/subhapriyo/sas_forcex.git --branch version-16
bench --site <site> install-app sas_forcex
bench build --app sas_forcex
```

Installing fills **ForceX Theme Settings** with the ForceX defaults.

## Updating a server

```bash
cd ~/frappe-bench
bench --site <site> backup

cd apps/sas_forcex
git pull upstream version-16      # or: origin — check with `git remote -v`

cd ~/frappe-bench
bench --site <site> migrate       # every site that has sas_forcex installed
bench build --app sas_forcex
bench --site <site> clear-cache
bench restart                     # or: sudo supervisorctl restart all
```

The pulled code applies to every site on the bench, so migrate all sites that have
sas_forcex installed. To list them:

```bash
for s in $(ls sites | grep -v -e apps -e assets -e '\.json$' -e '\.txt$'); do
  bench --site $s list-apps 2>/dev/null | grep -q sas_forcex && echo $s
done
```

In development (`bench start`), restart `bench start` after pulling so the new Python code loads.

## Testing

```bash
# from apps/sas_forcex — no site needed
python -m unittest discover -s sas_forcex/tests -t .     # theme engine, DocType schema, package layout
node --test sas_forcex/tests_js/*.test.cjs                # Desk JS bundles

# needs a site
bench --site <site> run-tests --module sas_forcex.sas_forcex.doctype.forcex_theme_settings.test_forcex_theme_settings
```

## Contributing

This app uses `pre-commit` for formatting and linting (ruff, eslint, prettier, pyupgrade):

```bash
cd apps/sas_forcex
pre-commit install
```

## CI

GitHub Actions:

- **CI** — installs the app and runs the unit tests on every push to `version-16`.
- **Linters** — runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and
  [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.

## License

MIT — see `license.txt`.
