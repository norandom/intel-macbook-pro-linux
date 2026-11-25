"""Nix user CLI tools (spec nix-user-tools): tool list, rendered flake inputs, PATH snippets.

The flake lives in nix/ (flake.nix + committed flake.lock). The deploy copies it with a
config-rendered tools.json to ~/.local/share/t2-mac-kde/nix/ and builds the profile from
there, so the repository tree never depends on the user's config.
"""
from __future__ import annotations

import hashlib
import json
import re

# Attribute names in nixpkgs nixos-26.05 (checked against pkgs/by-name and all-packages.nix).
# Not here: upmd, dagger, pwndbg (not in nixpkgs; pwndbg was removed), rc (nixpkgs "rc" is the Plan 9 shell, not
# rustfs-cli), uv (bootstrap needs it before Nix), node/npm (nvm) and rustup (Ubuntu archive:
# nixpkgs' rustup patches every toolchain it downloads to Nix's glibc; see manage/rust_toolchains.py).
DEFAULT_TOOLS = (
    "zellij", "kubectl", "kubernetes-helm", "k9s", "ktop", "bitwarden-cli", "rclone", "lazydocker", "ctop",
    "btop", "ripgrep", "fd", "bat", "jq", "fzf", "lazygit", "glow", "gh", "gdu", "trippy",
    "multitail", "aria2", "go", "nim", "nimble", "nimlangserver", "nano-syntax-highlighting",
    "netcat-openbsd", "gef", "rizin", "valgrind", "lftp", "byobu", "eza", "uutils-coreutils",
    "atuin", "delta", "yazi", "zoxide",
)

# Application-catalog ids that were GitHub-release binaries before -> nixpkgs attribute.
# While the attribute is in nix_tools, Nix owns the tool; remove it from nix_tools and the
# release route (tasks/apps.py) installs it again.
MIGRATED = {
    "zellij": "zellij", "kubectl": "kubectl", "helm": "kubernetes-helm", "k9s": "k9s",
    "ktop": "ktop", "bw": "bitwarden-cli", "rclone": "rclone",
}
# Catalog ids installed by apt (system-wide, stay installed) that Nix shadows in the user's PATH.
NIX_PREFERRED = {
    "btop": "btop", "ripgrep": "ripgrep", "fd-find": "fd", "bat": "bat", "jq": "jq", "fzf": "fzf",
    "lazygit": "lazygit", "glow": "glow", "gh": "gh", "gdu": "gdu", "trippy": "trippy",
    "multitail": "multitail", "aria2": "aria2", "golang-go": "go",
}

_ATTR = re.compile(r"[A-Za-z_][A-Za-z0-9_'-]*")


def tools(value=None) -> tuple[str, ...]:
    """Validated, de-duplicated tool list (config nix_tools; None = repository default)."""
    if value is None:
        return DEFAULT_TOOLS
    if isinstance(value, str) or not all(isinstance(v, str) for v in value):
        raise ValueError("nix_tools must be a list of nixpkgs attribute names")
    seen: list[str] = []
    for name in value:
        if not _ATTR.fullmatch(name):
            raise ValueError(f"nix_tools: {name!r} is not a top-level nixpkgs attribute name")
        if name not in seen:
            seen.append(name)
    return tuple(seen)


def tools_json(selected) -> str:
    return json.dumps(list(selected), indent=2) + "\n"


def stamp(flake: bytes, lock: bytes, tools_text: bytes) -> str:
    """Same value as `cat flake.nix flake.lock tools.json | sha256sum` in t2-nix-update."""
    return hashlib.sha256(flake + lock + tools_text).hexdigest()


# --- PATH: Nix profile first --------------------------------------------------------------
# Markers are regexes for pyinfra files.block: no ()[]*+?|^$\ in them.
PATH_MARKER = "# {mark} t2-mac-kde: nix tools first in PATH"
# The block goes in front of the ble.sh attach block (which must stay last), else at the end,
# i.e. after the developer-tools block that prepends ~/.local/bin.
BLESH_ATTACH_LINE = "BEGIN t2-mac-kde: ble.sh attach"
PATH_BLOCK = '''if [ -d "$HOME/.nix-profile/bin" ]; then
    __t2_p=":$PATH:"; __t2_p=${__t2_p//":$HOME/.nix-profile/bin:"/:}; __t2_p=${__t2_p#:}; __t2_p=${__t2_p%:}
    export PATH="$HOME/.nix-profile/bin${__t2_p:+:$__t2_p}"; unset __t2_p
fi'''
# POSIX sh for uwsm env-hyprland (sourced before Hyprland starts).
SESSION_PATH = ('if [ -d "$HOME/.nix-profile/bin" ]; then\n'
                '  case ":$PATH:" in *":$HOME/.nix-profile/bin:"*) ;; '
                '*) export PATH="$HOME/.nix-profile/bin:$PATH" ;; esac\n'
                'fi\n')

GC_UNITS = {
    "nix-gc.service": """[Unit]
Description=Nix: delete profile generations older than 30 days and collect garbage

[Service]
Type=oneshot
# sg: the user manager may predate the nix-users membership (linger); sg picks it up.
ExecStart=/usr/bin/sg nix-users -c "/usr/bin/nix-collect-garbage --delete-older-than 30d"
Nice=19
IOSchedulingClass=idle
""",
    "nix-gc.timer": """[Unit]
Description=Weekly Nix garbage collection

[Timer]
OnCalendar=weekly
Persistent=true
RandomizedDelaySec=1h

[Install]
WantedBy=timers.target
""",
}
