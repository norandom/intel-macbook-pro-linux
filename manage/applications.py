"""Application inventory ported from the source tasks/apps.py (+ desktop.py terminator/xfe).

Source: norandom/hyperland-forky-worker-vm @ a1c09ec3f02a98b7c6a4641f907108a2ad080993
(tasks/apps.py, tasks/base.py, tasks/desktop.py, group_data/all.py).

Every source entry appears exactly once in CATALOG with a disposition:
  native    installed here from the Ubuntu archive (manage.packages guard)
  release   pinned upstream release binary into ~/.local/bin (sha256 verified)
  delegated installed by another spec (owner named)
  excluded  intentionally not ported on this laptop
  blocked   no permitted route yet (vendor apt repo / .deb / Snap-only)
  backlog   deferred by the owner (docs/backlog.md)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

SOURCE_REVISION = "a1c09ec3f02a98b7c6a4641f907108a2ad080993"

# id -> (Ubuntu package, executable). Installed by tasks/apps.py.
NATIVE = {
    "aria2": ("aria2", "aria2c"),
    "atop": ("atop", "atop"),
    "c3270": ("c3270", "c3270"),
    "x3270": ("x3270", "x3270"),
    "gdu": ("gdu", "gdu"),
    "gh": ("gh", "gh"),  # source: cli.github.com vendor repo; Ubuntu ships it natively
    "glow": ("glow", "glow"),
    "golang-go": ("golang-go", "go"),
    "lazygit": ("lazygit", "lazygit"),
    "meld": ("meld", "meld"),
    "multitail": ("multitail", "multitail"),
    "nedit": ("nedit", "nedit"),
    "posting": ("posting", "posting"),
    "qpdfview": ("qpdfview", "qpdfview"),
    "ristretto": ("ristretto", "ristretto"),
    "rsync": ("rsync", "rsync"),
    "rust-coreutils": ("rust-coreutils", "coreutils"),
    "trippy": ("trippy", "trip"),
    "xpdf": ("xpdf", "xpdf"),
    "foot": ("foot", "foot"),
    "xfce4-terminal": ("xfce4-terminal", "xfce4-terminal"),
    # source desktop.py auxiliary apps (hyprland-core profile)
    "terminator": ("terminator", "terminator"),
    # source: Debian forky .deb from mkasberg/ghostty-ubuntu; Ubuntu 26.04 ships it natively
    "ghostty": ("ghostty", "ghostty"),
}

# name -> (version, url, sha256), verbatim from source group_data/all.py release_tools.
RELEASE_TOOLS = {
    "zellij": ("0.45.1", "https://github.com/zellij-org/zellij/releases/download/v0.45.1/zellij-x86_64-unknown-linux-musl.tar.gz",
               "40bcc2e03f5d5ae8e054e39f676081fe12ab70871506996ba595834c3718eefc"),
    "upmd": ("0.2.7", "https://github.com/rezigned/upmd/releases/download/v0.2.7/upmd-x86_64-unknown-linux-gnu.tar.xz",
             "101336d7a8f4648a3bf894d5636875f1df3d219719d470096c562e0cf4d6b9aa"),
    "kubectl": ("1.37.1", "https://dl.k8s.io/release/v1.37.1/bin/linux/amd64/kubectl",
                "65691ff77eb6fa44c908b77a1082c9f092c3b9733b5cefabec0d1104890e21a8"),
    "helm": ("4.3.0", "https://get.helm.sh/helm-v4.3.0-linux-amd64.tar.gz",
             "86584a54def73570558f66f5111cc53dfed56689637ae32c1201205d494f54fb"),
    "k9s": ("0.51.0", "https://github.com/derailed/k9s/releases/download/v0.51.0/k9s_Linux_amd64.tar.gz",
            "c3752ad51a5a4015a113819c4eeb6e55a4d0e4b8e652494797532f6fc8161dd7"),
    "ktop": ("0.5.3", "https://github.com/vladimirvivien/ktop/releases/download/v0.5.3/ktop_v0.5.3_linux_amd64.tar.gz",
             "f8104e5d09bb764da014ba87e5f75c73f55a26b907e9699f43176848a33dbea6"),
    "bw": ("2026.9.1", "https://github.com/bitwarden/clients/releases/download/cli-v2026.9.1/bw-linux-2026.9.1.zip",
           "84289eaf59d691f04242605112f21b00e8dba65acdedbc60dde001a2860f2097"),
    "rc": ("0.1.36", "https://github.com/rustfs/cli/releases/download/v0.1.36/rustfs-cli-linux-amd64-v0.1.36.tar.gz",
           "4a8128911ccad4e7b481f26635a4cfd1ec064412210526e57ad2c748d356f3b7"),
    "rclone": ("1.75.2", "https://github.com/rclone/rclone/releases/download/v1.75.2/rclone-v1.75.2-linux-amd64.zip",
               "349ac8fba6ff65d6247043f1750cdcb518ec5d500ef91463a10d37c0ccdf3702"),
}

_FOUNDATION = "local-system-foundation (tasks/tools.py)"
_LIBREOFFICE = "LibreOffice deferred (docs/backlog.md)"
_CRAFT = "Craft suite deferred (docs/backlog.md)"
_VENDOR = "vendor apt repo / .deb route not permitted by the application-suite spec yet"

# id -> (disposition, owner, executable or None, reason)
OTHER = {
    # foundation CLI list (installed there, observed here)
    **{p: ("delegated", _FOUNDATION, exe, None) for p, exe in (
        ("git", "git"), ("bat", "batcat"), ("fd-find", "fdfind"), ("fzf", "fzf"), ("gcc", "gcc"),
        ("make", "make"), ("ripgrep", "rg"), ("tree", "tree"), ("unzip", "unzip"), ("neovim", "nvim"),
        ("curl", "curl"), ("ca-certificates", None), ("jq", "jq"), ("htop", "htop"), ("btop", "btop"))},
    "cliphist": ("delegated", "hyprland-desktop", "cliphist", None),
    "x11-xserver-utils": ("delegated", "desktop-fonts", "xset", None),
    "podman-tui": ("delegated", "rootless-containers", "podman-tui", None),
    "dbus-user-session": ("delegated", "hyprland-desktop", None, None),
    "systemd-zram-generator": ("delegated", "laptop-resource-policy", None, None),
    "earlyoom": ("delegated", "laptop-resource-policy", "earlyoom", None),
    "nodejs": ("excluded", "shell-user-tools", "node", "system Node replaced by user nvm"),
    "npm": ("excluded", "shell-user-tools", "npm", "system npm replaced by user nvm"),
    "sudo": ("excluded", "system", "sudo", "already part of the Ubuntu install"),
    "qemu-guest-agent": ("excluded", "none", None, "VM-only; this is a laptop"),
    "littlesnitch": ("excluded", "none", None, "source purge-only entry; not ported"),
    "xfe": ("delegated", "tasks/xfe.py", "xfe",
            "Ubuntu xfe 2.1.1-1 unpacked to /usr/local (its Conflicts: im-config would remove a KDE-base package)"),
    "chromium": ("blocked", "application-suite", "chromium", "Ubuntu only ships a Snap transition package"),
    "chromium-driver": ("blocked", "application-suite", "chromedriver", "Ubuntu only ships a Snap transition package"),
    "sublime-text": ("blocked", "application-suite", "subl", _VENDOR),
    "typora": ("blocked", "application-suite", "typora", _VENDOR),
    "vivaldi-stable": ("blocked", "application-suite", "vivaldi", _VENDOR + "; an existing install is left untouched"),
    "obsidian": ("blocked", "application-suite", "obsidian", _VENDOR),
    "bitwarden": ("blocked", "application-suite", "bitwarden", _VENDOR),
    "quarto": ("blocked", "application-suite", "quarto", _VENDOR + " (source client role)"),
    "positron": ("blocked", "application-suite", "positron", _VENDOR + " (source client role)"),
    "code": ("blocked", "application-suite", "code", _VENDOR + " (source client role)"),
    **{p: ("backlog", "application-suite", None, _LIBREOFFICE) for p in (
        "libreoffice-calc", "libreoffice-writer", "libreoffice-gtk3", "libreoffice-l10n-de",
        "fonts-crosextra-carlito", "hunspell-de-de", "hunspell-en-us", "hyphen-de", "hyphen-en-us",
        "mythes-de", "mythes-en-us")},
    **{p: ("backlog", "application-suite", None, _CRAFT) for p in (
        "pdfcraft", "designcraft", "gridcraft", "lightcraft", "wordcraft", "deckcraft", "cadcraft")},
}


def catalog() -> dict[str, tuple[str, str, str | None, str | None]]:
    """id -> (disposition, owner, executable, reason) for every source entry."""
    entries = {i: ("native", "application-suite", exe, None) for i, (_, exe) in NATIVE.items()}
    entries.update({n: ("release", "application-suite", n, None) for n in RELEASE_TOOLS})
    overlap = set(entries) & set(OTHER)
    if overlap:
        raise RuntimeError(f"Application ids owned twice: {sorted(overlap)}")
    entries.update(OTHER)
    return entries


def native_packages() -> tuple[str, ...]:
    return tuple(pkg for pkg, _ in NATIVE.values())


def _dpkg_version(package: str) -> str | None:
    try:
        out = subprocess.run(["dpkg-query", "-W", "-f=${db:Status-Status} ${Version}", package],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    status, _, version = out.stdout.partition(" ")
    return version if out.returncode == 0 and status == "installed" else None


def observe(home: str | None = None) -> list[dict]:
    """Read-only availability probe (actual executables on PATH + ~/.local/bin)."""
    home = home or os.path.expanduser("~")
    path = os.pathsep.join((f"{home}/.local/bin", os.environ.get("PATH", "/usr/bin:/bin")))
    report = []
    for app_id, (disposition, owner, exe, reason) in sorted(catalog().items()):
        resolved = shutil.which(exe, path=path) if exe else None
        version = None
        if disposition == "native":
            version = _dpkg_version(NATIVE[app_id][0])
        elif disposition == "release":
            version = RELEASE_TOOLS[app_id][0] if resolved else None
        report.append({
            "id": app_id, "owner": owner, "disposition": disposition,
            "selected": disposition in ("native", "release"),
            "installed_version": version, "executable": resolved or exe,
            "available": bool(resolved), "reason": reason,
        })
    return report


def report_path(home: str | None = None) -> Path:
    home = home or os.path.expanduser("~")
    state = os.environ.get("XDG_STATE_HOME") or f"{home}/.local/state"
    return Path(state) / "t2-mac-kde" / "applications.json"


def write_report(home: str | None = None) -> Path:
    """Write $XDG_STATE_HOME/t2-mac-kde/applications.json (schema_version 1) atomically."""
    target = report_path(home)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema_version": 1, "source_revision": SOURCE_REVISION,
            "entries": {e["id"]: e for e in observe(home)}}
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, target)
    return target


if __name__ == "__main__":  # quick read-only status: python -m manage.applications
    for e in observe():
        state = "ok" if e["available"] else ("MISSING" if e["selected"] else "-")
        print(f"{e['id']:24} {e['disposition']:9} {state:8} {e['reason'] or e['owner']}")
