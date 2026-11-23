"""Vendor app routes: pinned keys, .debs, tarballs, repo lines and pins (offline)."""
import hashlib
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

from manage import applications as apps
from manage.packages import _LOCAL_DEB, LOCAL_DEBS

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "files/vendor-apps"
TASK = (ROOT / "tasks/vendor_apps.py").read_text()
DEB_HOSTS = {"obsidian": "github.com", "penguin-mail": "github.com", "bitwarden": "github.com", "quarto": "github.com",
             "positron": "cdn.posit.co", "remotedesktopmanager": "cdn.devolutions.net",
             "zoom": "cdn.zoom.us", "slack": "downloads.slack-edge.com", "discord": "dl.discordapp.net",
             "rclone-ui": "github.com", "1-1": "github.com"}
DEB_PATHS = {"obsidian": "/obsidianmd/obsidian-releases/", "penguin-mail": "/c9dev/penguin-mail/releases/download/v", "bitwarden": "/bitwarden/clients/releases/download/desktop-v",
             "quarto": "/quarto-dev/quarto-cli/", "rclone-ui": "/rclone-ui/rclone-ui/releases/download/v",
             "1-1": "/norandom/1-1/releases/download/v"}
TARBALL_HOSTS = {"mendeley": "static.mendeley.com"}   # default: github.com
TARBALL_PATHS = {"mendeley": "/bin/desktop/mendeley-reference-manager-", "zed": "/zed-industries/zed/", "telegram": "/telegramdesktop/tdesktop/", "zen": "/zen-browser/desktop/",
                 "podman-desktop": "/podman-desktop/podman-desktop/", "xtool": "/xtool-org/xtool/"}


class RepoTests(unittest.TestCase):
    def test_key_pins_match_committed_files(self):
        for app_id, (name, _pkgs, _exe, sha) in apps.VENDOR_REPOS.items():
            data = (SRC / f"{name}-keyring.gpg").read_bytes()
            self.assertFalse(data.startswith(b"-----BEGIN"), name)  # dearmored binary keyring
            self.assertEqual(hashlib.sha256(data).hexdigest(), sha, app_id)

    def test_list_lines_are_https_signed_by_our_keyring(self):
        for name, *_ in apps.VENDOR_REPOS.values():
            lines = [l for l in (SRC / f"{name}.list").read_text().splitlines() if l and not l.startswith("#")]
            self.assertEqual(len(lines), 1, name)
            self.assertRegex(lines[0], rf"^deb \[arch=amd64 signed-by=/usr/share/keyrings/{name}-archive-keyring\.gpg\] https://")

    def test_vscode_repo_is_not_duplicated_by_its_postinst(self):
        self.assertIn("code code/add-microsoft-repo boolean false", TASK)
        self.assertNotEqual(apps.VENDOR_REPOS["code"][0], "vscode")  # vscode.list would be rewritten by postinst

    def test_mozilla_repo_may_only_supply_devedition(self):
        text = (SRC / "90-t2-mozilla.pref").read_text()
        blocks = [dict(l.split(": ", 1) for l in b.splitlines() if not l.startswith("#"))
                  for b in text.strip().split("\n\n")]
        self.assertEqual(blocks, [
            {"Package": "*", "Pin": "origin packages.mozilla.org", "Pin-Priority": "-1"},
            {"Package": "firefox-devedition firefox-devedition-l10n-*", "Pin": "origin packages.mozilla.org",
             "Pin-Priority": "1000"},
            {"Package": "firefox", "Pin": "release o=Ubuntu", "Pin-Priority": "-1"},
        ])
        self.assertEqual(apps.VENDOR_REPOS["firefox-devedition"][1], ("firefox-devedition", "firefox-devedition-l10n-de"))
        self.assertIn("90-t2-mozilla.pref", TASK)

    def test_xtradeb_ppa_may_only_supply_chromium(self):
        text = (SRC / "90-t2-xtradeb.pref").read_text()
        blocks = [dict(l.split(": ", 1) for l in b.splitlines() if not l.startswith("#"))
                  for b in text.strip().split("\n\n")]
        self.assertEqual(blocks[0], {"Package": "*", "Pin": "release o=LP-PPA-xtradeb-apps", "Pin-Priority": "-1"})
        self.assertEqual(blocks[1]["Pin"], "release o=LP-PPA-xtradeb-apps")
        self.assertTrue(set(blocks[1]["Package"].split()) <= {"chromium", "chromium-common", "chromium-driver",
                                                             "chromium-sandbox", "chromium-l10n"})
        self.assertNotIn("snapd", text)
        self.assertEqual(apps.VENDOR_REPOS["chromium"][1], ("chromium", "chromium-driver"))


    def test_oneapi_installs_compiler_only_without_env(self):
        name, packages, exe, _sha = apps.VENDOR_REPOS["intel-oneapi"]
        self.assertEqual(packages, ("intel-oneapi-compiler-dpcpp-cpp",))
        self.assertEqual(exe, "/opt/intel/oneapi/compiler/latest/bin/icx")
        self.assertNotRegex(TASK, r"setvars|\bCC=|\bCXX=|bashrc")


    def test_vtune_is_not_installed(self):
        # its postinst builds and loads kernel modules (protected boundary)
        self.assertFalse(any("vtune" in p for _n, pkgs, *_ in apps.VENDOR_REPOS.values() for p in pkgs))
        self.assertEqual(apps.catalog()["intel-oneapi-vtune"][0], "blocked")


class PinnedDownloadTests(unittest.TestCase):
    def test_debs_are_pinned_https_vendor_urls(self):
        for app_id, (package, version, url, sha, _exe) in apps.VENDOR_DEBS.items():
            parsed = urlparse(url)
            self.assertEqual(parsed.scheme, "https", app_id)
            self.assertEqual(parsed.hostname, DEB_HOSTS[app_id], app_id)
            self.assertTrue(parsed.path.startswith(DEB_PATHS.get(app_id, "/")), app_id)
            self.assertRegex(sha, r"\A[0-9a-f]{64}\Z", app_id)
            self.assertIn(version.split("+")[0], url, app_id)
            self.assertTrue(_LOCAL_DEB.match(f"{LOCAL_DEBS}/{package}_{version}.deb"), app_id)

    def test_tarballs_are_pinned_github_releases(self):
        for app_id, (version, url, sha, _exe) in apps.VENDOR_TARBALLS.items():
            parsed = urlparse(url)
            self.assertEqual((parsed.scheme, parsed.hostname), ("https", TARBALL_HOSTS.get(app_id, "github.com")), app_id)
            self.assertTrue(parsed.path.startswith(TARBALL_PATHS[app_id]), app_id)
            self.assertIn(version, url, app_id)
            self.assertRegex(sha, r"\A[0-9a-f]{64}\Z", app_id)

    def test_downloads_are_sha256_checked_before_install(self):
        self.assertIn("sha256sum -c", TASK)
        self.assertNotRegex(TASK, r"dpkg -i|apt-get install|--no-sandbox|curl[^\n]*\| *(ba)?sh")


class ConfigTests(unittest.TestCase):
    def test_slack_cron_never_adds_its_repo(self):
        self.assertIn('repo_add_once="false"\\nrepo_reenable_on_distupgrade="false"', TASK)
        self.assertIn('dest="/etc/default/slack"', TASK)

    def test_zoom_wayland_share_keeps_other_keys(self):
        import tempfile
        ns = {}
        src = TASK[TASK.index("def _zoom_wayland_share"):TASK.index("python.call(name=\"Zoom")]
        with tempfile.TemporaryDirectory() as home:
            conf = Path(home, ".config/zoomus.conf")
            conf.parent.mkdir()
            conf.write_text("[General]\nenableWaylandShare=false\nxwayland=true\n[AS]\nx=1\n")
            exec(src, {"Path": Path, "os": __import__("os"), "home": home}, ns)
            ns["_zoom_wayland_share"]()
            ns["_zoom_wayland_share"]()
            self.assertEqual(conf.read_text(), "[General]\nenableWaylandShare=true\nxwayland=true\n[AS]\nx=1\n")
            conf.unlink()
            ns["_zoom_wayland_share"]()
            self.assertEqual(conf.read_text(), "[General]\nenableWaylandShare=true\n")


class AppArmorTests(unittest.TestCase):
    def test_profiles_are_ubuntu_style_userns_only(self):
        for name, binary in (("t2-zen", "/home/*/.local/opt/zen-*/zen/zen{,-bin}"),
                             ("t2-podman-desktop", "/home/*/.local/opt/podman-desktop-*/podman-desktop"),
                             ("t2-mendeley", "/home/*/.local/opt/mendeley-*/mendeley-reference-manager")):
            text = (SRC / name).read_text()
            self.assertIn(f"profile {name} {binary} flags=(unconfined) {{", text)
            self.assertIn("  userns,", text)
            self.assertIn(f"include if exists <local/{name}>", text)


class CatalogTests(unittest.TestCase):
    def test_vendor_routes_are_catalogued(self):
        cat = apps.catalog()
        for app_id in (*apps.VENDOR_REPOS, *apps.VENDOR_DEBS, *apps.VENDOR_TARBALLS, "chromium-driver"):
            self.assertEqual(cat[app_id][0], "vendor", app_id)
            self.assertEqual(cat[app_id][1], "tasks/vendor_apps.py", app_id)
        self.assertEqual(cat["vivaldi-stable"][0], "vendor")  # owner decision 2026-11-16

    def test_vivaldi_replaces_its_own_repo_entry(self):
        task = (ROOT / "tasks/vendor_apps.py").read_text()
        self.assertIn('path="/etc/apt/sources.list.d/vivaldi.sources", present=False', task)
        self.assertIn('repo_add_once="false"', task)


if __name__ == "__main__":
    unittest.main()


class PinnedDebTests(unittest.TestCase):
    def test_newer_installed_deb_is_kept(self):
        from unittest import mock
        with mock.patch.object(apps, "_dpkg_version", return_value="0.2.0-beta.1"):
            self.assertFalse(apps.needs_pinned_deb("1-1", "0.1.0-beta.1"))
            self.assertFalse(apps.needs_pinned_deb("1-1", "0.2.0-beta.1"))
        with mock.patch.object(apps, "_dpkg_version", return_value="0.1.0-alpha.7"):
            self.assertTrue(apps.needs_pinned_deb("1-1", "0.1.0-beta.1"))
        with mock.patch.object(apps, "_dpkg_version", return_value=None):
            self.assertTrue(apps.needs_pinned_deb("1-1", "0.1.0-beta.1"))
