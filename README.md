### ForceX (sas_forcex)

The ForceX platform layer, installed on every tenant:

| Path | What it is |
| --- | --- |
| `public/css/forcex_desk_theme.bundle.css` | ForceX palette for the whole Desk (via Desk CSS variables) |
| `public/css/forcex_components.bundle.css` | `.fx-*` design system used by the `forcex.ui` helpers |
| `public/js/forcex_rebrand.bundle.js` | Replaces Frappe / ERPNext / HRMS names with ForceX names in the UI |
| `public/js/forcex_ui.bundle.js` | Generic `forcex.ui` component kit + `themeForms()` |
| `tests_js/` | Node unit tests for both JS bundles |

Product features live in their own apps, e.g. **sas_forcex_fleeto** (FLEETO Service & Warranty).

### Testing

```bash
# from apps/sas_forcex
node --test sas_forcex/tests_js/*.test.cjs
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
