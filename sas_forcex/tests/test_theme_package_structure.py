"""Guards for the shape of sas_forcex/forcex_theme/ (see its __init__ for the layout).

1. No Frappe import: the theme logic must stay testable without a site.
2. Layering: each file may only import from files above it in LAYERS, so there are
   no cycles and anyone can read the package top to bottom.
"""

import ast
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "forcex_theme"
LAYERS = ["colours", "schema", "rules", "css", "branding", "client", "transfer"]


def _imports(path):
	tree = ast.parse(path.read_text(encoding="utf-8"))
	for node in ast.walk(tree):
		if isinstance(node, ast.Import):
			yield from (alias.name for alias in node.names)
		elif isinstance(node, ast.ImportFrom):
			yield ("." * node.level) + (node.module or "")


class TestThemePackageStructure(unittest.TestCase):
	def test_every_module_is_listed_in_the_layers(self):
		found = sorted(p.stem for p in PKG.glob("*.py") if p.stem != "__init__")
		self.assertEqual(found, sorted(LAYERS))

	def test_no_frappe_import(self):
		for path in PKG.glob("*.py"):
			for name in _imports(path):
				self.assertFalse(name.split(".")[0] == "frappe", f"{path.name} imports {name}")

	def test_each_file_only_imports_files_above_it(self):
		for i, layer in enumerate(LAYERS):
			allowed = set(LAYERS[:i])
			for name in _imports(PKG / f"{layer}.py"):
				if name.startswith("."):
					self.assertIn(name.lstrip("."), allowed, f"{layer}.py imports {name}")
