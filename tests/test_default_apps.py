import unittest

from manage.default_apps import entries


class DefaultAppsTests(unittest.TestCase):
    def test_valid(self):
        table = {"text/html": "vivaldi-stable.desktop", "x-scheme-handler/https": "vivaldi-stable.desktop",
                 "application/pdf": "ai.storyteller.pdfcraft.desktop"}
        self.assertEqual(dict(entries(table)), table)

    def test_stray_setting_is_reported_with_a_hint(self):
        with self.assertRaisesRegex(RuntimeError, "scrivener = True.*above that table"):
            entries({"text/html": "vivaldi-stable.desktop", "scrivener": True})
        for bad in ({"text/html": "vivaldi"}, {"text/html": "a b.desktop"}, {"html": "x.desktop"}, []):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                entries(bad)


if __name__ == "__main__":
    unittest.main()
