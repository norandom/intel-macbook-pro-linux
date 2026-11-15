"""Owner-approved vendor apps: official apt repos, pinned vendor .debs, pinned user tarballs.

Run: .venv/bin/pyinfra @local tasks/vendor_apps.py [--dry] [--use-sudo-password]

- Repos (Sublime Text, VS Code, Typora, XtraDeb Chromium): committed signing key, sha256
  checked here before anything; deb line with signed-by; first install refreshes only that
  source and goes through the guarded root helper (manage.packages). Updates via apt.
- .debs (Obsidian, Bitwarden, Quarto, Positron, Remote Desktop Manager, Zoom, Slack, Discord): pinned version, URL,
  sha256; staged in /var/cache/t2-mac-kde/debs and installed by the guarded helper, which
  scans the archive. Re-run with new pins to update.
- Tarballs (Zed, Zen, Podman Desktop): user-level in ~/.local/opt/<id>-<version>, no sudo
  except the AppArmor userns profiles for Zen and Podman Desktop.
Pins live in manage/applications.py (VENDOR_REPOS / VENDOR_DEBS / VENDOR_TARBALLS).
Re-run tasks/themes.py afterwards: it only themes Sublime/VS Code/Positron once they exist.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
from io import StringIO

from pyinfra import logger
from pyinfra.operations import files, python, server

from manage.applications import VENDOR_DEBS, VENDOR_REPOS, VENDOR_TARBALLS, _dpkg_version
from manage.packages import LOCAL_DEBS
from manage.preflight import validate_local_context

validate_local_context()
project = Path(__file__).resolve().parents[1]
src = project / "files/vendor-apps"
home = os.path.expanduser("~")
opt, bin_dir, apps_dir = f"{home}/.local/opt", f"{home}/.local/bin", f"{home}/.local/share/applications"
helper = "cd " + shlex.quote(str(project)) + " && /usr/bin/python3 -m manage.packages --apply "
CURL = "curl -fsSL --proto '=https' --tlsv1.2"

for name, _pkgs, _exe, sha in VENDOR_REPOS.values():
    if hashlib.sha256((src / f"{name}-keyring.gpg").read_bytes()).hexdigest() != sha:
        raise RuntimeError(f"{name} archive key does not match the pinned sha256.")


def _refresh(name):
    return (f"apt-get update -o Dir::Etc::sourcelist=sources.list.d/{name}.list "
            "-o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0")


# --- Official apt repos ------------------------------------------------------------
# XtraDeb carries many apps (firefox, ...): pin it to Chromium only, before its list exists.
files.put(name="XtraDeb PPA pin (chromium packages only)", src=str(src / "90-t2-xtradeb.pref"),
          dest="/etc/apt/preferences.d/90-t2-xtradeb.pref", mode="0644", _sudo=True)
for app_id, (name, packages, exe, _sha) in VENDOR_REPOS.items():
    files.put(name=f"{name} archive key", src=str(src / f"{name}-keyring.gpg"),
              dest=f"/usr/share/keyrings/{name}-archive-keyring.gpg", mode="0644", _sudo=True)
    files.put(name=f"{name} apt source", src=str(src / f"{name}.list"),
              dest=f"/etc/apt/sources.list.d/{name}.list", mode="0644", _sudo=True)
    missing = [p for p in packages if not _dpkg_version(p)]
    if missing or not shutil.which(exe):
        # VS Code's postinst would add its own vscode.sources + key; we own the repo entry.
        preseed = ("echo 'code code/add-microsoft-repo boolean false' | debconf-set-selections && "
                   if app_id == "code" else "")
        server.shell(name=f"Install {' '.join(packages)} (guarded, {name} repo)",
                     commands=preseed + _refresh(name) + " && " + helper + shlex.join(packages), _sudo=True)

# chromedriver drives the browser for AI agents: majors must match (same source package).
server.shell(
    name="chromedriver major == chromium major",
    commands=('c=$(chromium --version | grep -oE "[0-9]+" | head -1); d=$(chromedriver --version | grep -oE "[0-9]+" | head -1); '
              '[ -n "$c" ] && [ "$c" = "$d" ] || { echo "chromium $c vs chromedriver $d" >&2; exit 1; }'),
)

# --- Pinned vendor .debs -------------------------------------------------------------
# Slack's /etc/cron.daily/slack would add packagecloud's repo + unscoped keys in
# /etc/apt/trusted.gpg.d unless both flags are false; the pinned .deb is the update path.
files.put(name="Slack: no cron-added apt repo", dest="/etc/default/slack", mode="0644", _sudo=True,
          src=StringIO('# Managed by t2-mac-kde: updates come from the pinned .deb\n'
                       'repo_add_once="false"\nrepo_reenable_on_distupgrade="false"\n'))
for app_id, (package, version, url, sha, _exe) in VENDOR_DEBS.items():
    if _dpkg_version(package) == version:
        continue
    deb = f"{LOCAL_DEBS}/{package}_{version}.deb"
    server.shell(
        name=f"Install {package} {version} (pinned .deb, guarded)",
        commands=(f"mkdir -p {LOCAL_DEBS} && {CURL} -o {deb} {shlex.quote(url)} && "
                  f"echo '{sha}  {deb}' | sha256sum -c - && " + helper + deb),
        _sudo=True,
    )



def _zoom_wayland_share():
    """Zoom screen sharing through xdg-desktop-portal(-hyprland); only this key is touched.

    Audio stays on Zoom's default "Same as System" devices (no device keys written).
    """
    path = Path(home, ".config/zoomus.conf")
    lines = path.read_text().splitlines() if path.is_file() else []
    if "enableWaylandShare=true" in lines:
        return
    lines = [l for l in lines if not l.startswith("enableWaylandShare=")]
    if "[General]" not in lines:
        lines[:0] = ["[General]"]
    lines.insert(lines.index("[General]") + 1, "enableWaylandShare=true")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".conf.tmp")
    tmp.write_text("\n".join(lines) + "\n")
    os.replace(tmp, path)


python.call(name="Zoom: Wayland screen sharing via the portal (~/.config/zoomus.conf)", function=_zoom_wayland_share)

# --- Pinned user-level tarballs ----------------------------------------------------------


def _unpack(app_id, version, url, sha, strip=0):
    """Download, verify and extract into ~/.local/opt/<id>-<version> atomically."""
    dest = f"{opt}/{app_id}-{version}"
    archive = url.rsplit("/", 1)[1]
    server.shell(
        name=f"{app_id} {version} -> {dest} (sha256 verified)",
        commands=[f"""set -eu
mkdir -p "{opt}"; t=$(mktemp -d "{opt}/.t2-download.XXXXXX"); trap 'rm -rf "$t"' EXIT
{CURL} -o "$t/{archive}" "{url}"
echo "{sha}  $t/{archive}" | sha256sum -c --quiet
mkdir "$t/x"
tar --no-same-owner --strip-components={strip} -xf "$t/{archive}" -C "$t/x"
rm -rf "{dest}" && mv -T "$t/x" "{dest}" """],
    )
    return dest


def _apparmor(name):
    """Ubuntu-style unconfined userns profile (kernels with apparmor_restrict_unprivileged_userns)."""
    profile = files.put(name=f"AppArmor userns profile {name}", src=str(src / name),
                        dest=f"/etc/apparmor.d/{name}", mode="0644", _sudo=True)
    server.shell(name=f"Load AppArmor profile {name}", _if=profile.did_change, _sudo=True,
                 commands=f"[ \"$(cat /sys/module/apparmor/parameters/enabled 2>/dev/null)\" != Y ] || "
                          f"apparmor_parser -r /etc/apparmor.d/{name}")


# Zed: mirrors upstream script/install.sh (link bin/zed, copy + fix the .desktop file).
version, url, sha, _exe = VENDOR_TARBALLS["zed"]
zed = f"{opt}/zed-{version}/zed.app"
desktop = f"{apps_dir}/dev.zed.Zed.desktop"
if not os.access(f"{zed}/bin/zed", os.X_OK):
    _unpack("zed", version, url, sha)
files.link(name="~/.local/bin/zed", path=f"{bin_dir}/zed", target=f"{zed}/bin/zed", create_remote_dir=True)
if not (os.path.isfile(desktop) and zed in Path(desktop).read_text()):
    server.shell(name="Zed desktop entry", commands=[
        f'mkdir -p "{apps_dir}" && sed -e "s#^Icon=zed\\$#Icon={zed}/share/icons/hicolor/512x512/apps/zed.png#" '
        f'-e "s#^\\(Exec\\|TryExec\\)=zed#\\1={zed}/bin/zed#" "{zed}/share/applications/dev.zed.Zed.desktop" '
        f'> "{desktop}.new" && mv -f "{desktop}.new" "{desktop}"'])

# Zen: its own updater patches the install in place (user-writable), so the pin only
# matters for the first install; an existing ~/.local/opt/zen-* is kept as is.
version, url, sha, _exe = VENDOR_TARBALLS["zen"]
existing = sorted(Path(opt).glob("zen-*/zen/zen")) if os.path.isdir(opt) else []
zen = str(existing[-1].parent) if existing else f"{opt}/zen-{version}/zen"
if not existing:
    _unpack("zen", version, url, sha)
files.link(name="~/.local/bin/zen", path=f"{bin_dir}/zen", target=f"{zen}/zen", create_remote_dir=True)
files.put(name="Zen desktop entry (not set as default browser)", dest=f"{apps_dir}/zen.desktop", mode="644",
          create_remote_dir=True, src=StringIO(
              "[Desktop Entry]\nType=Application\nName=Zen Browser\nGenericName=Web Browser\n"
              f"Exec={zen}/zen %u\nIcon={zen}/browser/chrome/icons/default/default128.png\n"
              "Categories=Network;WebBrowser;\nMimeType=text/html;application/xhtml+xml;"
              "x-scheme-handler/http;x-scheme-handler/https;\nStartupWMClass=zen\nStartupNotify=true\n"
              "Terminal=false\n"))
_apparmor("t2-zen")

# Podman Desktop: talks to the rootless podman.socket from tasks/containers.py.
version, url, sha, _exe = VENDOR_TARBALLS["podman-desktop"]
pd = f"{opt}/podman-desktop-{version}"
if not os.access(f"{pd}/podman-desktop", os.X_OK):
    _unpack("podman-desktop", version, url, sha, strip=1)
files.link(name="~/.local/bin/podman-desktop", path=f"{bin_dir}/podman-desktop", target=f"{pd}/podman-desktop",
           create_remote_dir=True)
icon = f"{home}/.local/share/icons/hicolor/512x512/apps/podman-desktop.png"
files.put(name="Podman Desktop icon", src=str(src / "podman-desktop.png"), dest=icon, mode="644",
          create_remote_dir=True)
files.put(name="Podman Desktop desktop entry", dest=f"{apps_dir}/podman-desktop.desktop", mode="644",
          create_remote_dir=True, src=StringIO(
              "[Desktop Entry]\nType=Application\nName=Podman Desktop\nComment=Manage Podman containers\n"
              f"Exec={pd}/podman-desktop %U\nIcon={icon}\nCategories=Development;\n"
              "Terminal=false\n"))
_apparmor("t2-podman-desktop")


def _podman_desktop_no_self_update():
    """The pin is the update path: turn off its update check unless the user chose otherwise."""
    path = Path(home, ".local/share/containers/podman-desktop/configuration/settings.json")
    data = json.loads(path.read_text()) if path.is_file() else {}
    wanted = {"preferences.update.appUpdate": False, "preferences.update.reminder": "never"}
    if all(k in data for k in wanted):
        return
    data = {**wanted, **data}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, path)


python.call(name="Podman Desktop: no self-update (pin is the update path)", function=_podman_desktop_no_self_update)
logger.info("vendor_apps: re-run tasks/themes.py so Sublime/VS Code/Positron get their themes.")

# Zoom's .deb hard-depends on ibus. Pin this user's input method to "none" (im-config's
# own per-user file) so installing ibus never activates it: German dead keys / Option+L
# stay with XKB, and Xfe's ibus problem (its im-config conflict) cannot come back.
files.put(
    name="~/.xinputrc: input method none (keep ibus inactive)",
    src=StringIO("# Managed by t2-mac-kde (vendor_apps): ibus is installed for Zoom but not used.\nrun_im none\n"),
    dest=os.path.expanduser("~/.xinputrc"), mode="644",
)
