"""application-suite: inventory coverage, route rules and report shape (no apt, no network)."""
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manage import applications as apps

ROOT = Path(__file__).resolve().parents[1]

# Literal package lists of source tasks/apps.py + base.py tools, release/client maps, desktop.py apps.
SOURCE_ENTRIES = {
    "libreoffice-calc", "libreoffice-writer", "libreoffice-gtk3", "fonts-crosextra-carlito",
    "libreoffice-l10n-de", "hunspell-de-de", "hunspell-en-us", "hyphen-de", "hyphen-en-us",
    "mythes-de", "mythes-en-us", "chromium", "chromium-driver", "git", "atop", "neovim", "ripgrep",
    "fd-find", "fzf", "lazygit", "gcc", "make", "unzip", "rust-coreutils", "nodejs", "npm",
    "xfce4-terminal", "foot", "multitail", "bat", "tree", "aria2", "rsync", "cliphist", "golang-go",
    "meld", "glow", "posting", "trippy", "gdu", "ristretto", "qpdfview", "nedit", "xpdf", "x3270",
    "c3270", "x11-xserver-utils", "gh", "sublime-text", "typora", "vivaldi-stable", "obsidian",
    "bitwarden", "ghostty", "littlesnitch",
    "podman-tui", "zellij", "upmd", "kubectl", "helm", "k9s", "ktop", "bw", "rc", "rclone",
    "pdfcraft", "designcraft", "gridcraft", "lightcraft", "wordcraft", "deckcraft", "cadcraft",
    "quarto", "positron", "code",
    "sudo", "curl", "ca-certificates", "jq", "htop", "btop", "dbus-user-session",
    "systemd-zram-generator", "earlyoom", "qemu-guest-agent",
    "terminator", "xfe",
}
DISPOSITIONS = {"native", "release", "nix", "vendor", "delegated", "excluded", "blocked", "backlog"}


class CatalogTests(unittest.TestCase):
    def test_every_source_entry_has_one_disposition(self):
        cat = apps.catalog()
        self.assertEqual(SOURCE_ENTRIES - set(cat), set())
        for app_id, (disposition, owner, _exe, reason) in cat.items():
            self.assertIn(disposition, DISPOSITIONS, app_id)
            self.assertTrue(owner, app_id)
            if disposition in ("excluded", "blocked", "backlog"):
                self.assertTrue(reason, app_id)

    def test_no_prohibited_or_deferred_native_install(self):
        pkgs = set(apps.native_packages())
        self.assertFalse(pkgs & {"snapd", "snap", "flatpak", "chromium-browser", "chromium"})
        self.assertFalse({p for p in pkgs if p.startswith(("libreoffice", "hunspell", "hyphen", "mythes"))})
        self.assertNotIn("fonts-crosextra-carlito", pkgs)
        # foundation/neighbour-owned packages are not installed twice
        self.assertFalse(pkgs & {"bat", "fd-find", "fzf", "neovim", "git", "htop", "btop",
                                 "cliphist", "x11-xserver-utils", "nodejs", "npm"})
        self.assertIn("terminator", pkgs)
        self.assertNotIn("xfe", pkgs)  # conflicts with im-config (KDE)

    def test_release_tools_are_pinned_https_sha256(self):
        self.assertNotIn("podman-tui", apps.RELEASE_TOOLS)
        for name, (version, url, sha) in {**apps.RELEASE_TOOLS, **apps.RELEASE_FALLBACK}.items():
            self.assertTrue(url.startswith("https://"), name)
            self.assertIn(version, url, name)
            self.assertRegex(sha, r"\A[0-9a-f]{64}\Z", name)

    def test_no_vendor_repo_or_purge_in_deploy(self):
        text = (ROOT / "tasks/apps.py").read_text()
        for bad in ("sources.list", "/etc/apt", "purge", "apt-get", "dpkg -i", "snap", "flatpak", "_sudo"):
            self.assertNotIn(bad, text)


class ReportTests(unittest.TestCase):
    def test_report_distinguishes_available_and_missing(self):
        with tempfile.TemporaryDirectory() as home:
            for rel in (".local/bin/upmd", ".nix-profile/bin/zellij"):
                tool = Path(home, rel)
                tool.parent.mkdir(parents=True, exist_ok=True)
                tool.write_text("#!/bin/sh\n")
                tool.chmod(0o755)
            env = {"PATH": "/nonexistent", "XDG_STATE_HOME": f"{home}/state"}
            with patch.dict(os.environ, env), patch.object(apps, "_dpkg_version", return_value=None):
                path = apps.write_report(home)
            data = json.loads(path.read_text())
        self.assertEqual(path, Path(home, "state/t2-mac-kde/applications.json"))
        self.assertEqual(data["schema_version"], 1)
        upmd, zellij, helm = (data["entries"][i] for i in ("upmd", "zellij", "helm"))
        self.assertTrue(upmd["available"])
        self.assertEqual(upmd["installed_version"], "0.2.7")
        self.assertTrue(zellij["available"])  # found in ~/.nix-profile/bin
        self.assertEqual(zellij["disposition"], "nix")
        self.assertFalse(helm["available"])
        self.assertTrue(helm["selected"])
        self.assertTrue(data["entries"]["btop"]["nix_preferred"])
        self.assertFalse(data["entries"]["upmd"]["nix_preferred"])
        self.assertFalse(data["entries"]["libreoffice-calc"]["selected"])
        self.assertEqual(data["entries"]["vivaldi-stable"]["disposition"], "vendor")


class AssetTests(unittest.TestCase):
    def test_desktop_entries_are_valid_and_secret_free(self):
        for path in (ROOT / "files/applications").glob("*.desktop"):
            text = path.read_text()
            self.assertTrue(text.startswith("[Desktop Entry]"), path)
            self.assertNotRegex(text, re.compile(r"license|key=", re.I), path)


if __name__ == "__main__":
    unittest.main()
