"""tasks/office_apps.py pins and assets (offline: the task file is parsed, not executed)."""
import ast
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from manage import packages as guard

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks/office_apps.py"
OOR = "{http://openoffice.org/2001/registry}"


def constants() -> dict:
    tree = ast.parse(TASK.read_text())
    return {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id.isupper()}


def debs() -> dict:
    """Run only the pure debs() table builder from the task file."""
    tree = ast.parse(TASK.read_text())
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "debs")
    scope = dict(constants())
    exec(compile(ast.Module([func], []), str(TASK), "exec"), scope)
    return scope["debs"]()


class PinTests(unittest.TestCase):
    def test_pins_well_formed(self):
        table = debs()
        self.assertEqual(set(table), {"pdfcraft", "designcraft", "gridcraft", "lightcraft", "photocraft", "wordcraft",
                                      "deckcraft", "cadcraft", "open-idea"})
        for package, (version, url, sha) in table.items():
            with self.subTest(package=package):
                self.assertRegex(sha, r"\A[0-9a-f]{64}\Z")
                self.assertRegex(url, r"\Ahttps://github\.com/(storytold|l0ng-ai)/[a-z]+/releases/download/v")
                self.assertRegex(version, r"\A[0-9][0-9.]*(-1)?\Z")
                staged = f"{guard.LOCAL_DEBS}/{url.rsplit('/', 1)[1]}"
                self.assertRegex(staged, guard._LOCAL_DEB)
                guard.validate_request(guard.PackageRequest((staged,)))

    def test_openidea_bump_is_two_constants(self):
        c = constants()
        self.assertRegex(c["OPENIDEA_VERSION"], r"\A\d+\.\d+\.\d+\Z")
        self.assertIn(c["OPENIDEA_VERSION"], debs()["open-idea"][1])

    def test_libreoffice_packages_pass_the_guard(self):
        guard.validate_request(guard.PackageRequest(constants()["LIBREOFFICE"]))


class XcdTests(unittest.TestCase):
    def test_tabbed_ui_layer_parses(self):
        root = ET.parse(ROOT / "files/office-apps/t2-mac-kde.xcd").getroot()
        self.assertEqual(root.tag, OOR + "data")
        data = root.find(OOR + "component-data")
        self.assertEqual((data.get(OOR + "package"), data.get(OOR + "name")), ("org.openoffice.Office.UI", "ToolbarMode"))
        apps = {n.get(OOR + "name"): n.find("prop/value").text for n in data.find("node")}
        self.assertEqual(apps, {"Writer": "notebookbar.ui", "Calc": "notebookbar.ui"})
        self.assertTrue(constants()["XCD_DEST"].startswith("/usr/lib/libreoffice/share/registry/"))


if __name__ == "__main__":
    unittest.main()
