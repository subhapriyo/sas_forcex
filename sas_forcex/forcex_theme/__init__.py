"""ForceX theme — the logic, as plain Python (no Frappe import), so all of it is unit-tested
without a site. One file per concern; each may only import from the ones above it:

  colours.py   hex parsing, mixing, WCAG contrast
  schema.py    every setting: tabs, sections, labels, defaults → DEFAULTS, DocType fields
  rules.py     the one rulebook: coerce, validate a value, cross-field rules, readability
  css.py       --fxh-* tokens per mode, the <style> text, the baked-in default palette
  client.py    what the browser gets: Desk boot config, website/login <head> snippet
  transfer.py  export / import (dry-run preview, then apply)

How a saved value reaches the screen:
  ForceX Theme Settings → rules.coerce_settings → css.build_vars → --fxh-* custom property
  → public/css/forcex_harbour.bundle.css maps --fxh-* onto Frappe v16 tokens and selectors.

Frappe glue (hooks, endpoints, prefill) is in sas_forcex/theme.py. Other code imports
everything through sas_forcex.theme_engine, so the files here can be reorganised freely.
"""
