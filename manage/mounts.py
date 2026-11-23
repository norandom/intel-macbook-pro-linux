"""[[mounts]] in config.toml: network folders mounted at login (tasks/mounts.py, t2-mount).

    [[mounts]]
    name = "onedrive"              # unit t2-mount@onedrive, settings ~/.config/t2-mac-kde/mounts/<name>.env
    type = "rclone"                # rclone (cloud remotes; local VFS cache) or sshfs (SFTP; no cache)
    source = "OneDrive:"           # rclone remote[:path] / sshfs [user@]host:path (an ~/.ssh/config Host works)
    path = "~/OneDrive"            # mount point, under the home folder
    options = ["--onedrive-delta"] # rclone: extra flags (override the defaults); sshfs: extra -o options
    offline = ["Configs"]          # rclone only: folders kept fully in the cache (offline use)

Logins (rclone.conf, ssh keys) stay out of the config and the repository.
"""
from __future__ import annotations

import re
import shlex

TYPES = ("rclone", "sshfs")
_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,31}\Z")
_KEYS = {"name", "type", "source", "path", "options", "offline"}


def _text(value) -> bool:
    return isinstance(value, str) and value.strip() != "" and "\n" not in value and "\0" not in value


def entries(value, home: str) -> list[dict]:
    """Validated mounts (path expanded); raises RuntimeError naming the bad entry."""
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(m, dict) for m in value):
        raise RuntimeError("config.toml: mounts must be [[mounts]] tables")
    result, names, paths = [], set(), set()
    for m in value:
        label = f"[[mounts]] {m.get('name', '?')!r}"
        unknown = set(m) - _KEYS
        if unknown:
            raise RuntimeError(f"config.toml {label}: unknown keys {sorted(unknown)}")
        name, kind, source, path = m.get("name"), m.get("type"), m.get("source"), m.get("path")
        if not (isinstance(name, str) and _NAME.match(name)):
            raise RuntimeError(f"config.toml {label}: name must be lowercase letters, digits, '-'")
        if kind not in TYPES:
            raise RuntimeError(f"config.toml {label}: type must be one of {', '.join(TYPES)}")
        if not (_text(source) and ":" in source and not source.startswith("-")):
            raise RuntimeError(f"config.toml {label}: source must look like remote:path or host:path")
        if not (_text(path) and path.startswith("~/") and ".." not in path.split("/")):
            raise RuntimeError(f"config.toml {label}: path must be a folder under ~/ (e.g. \"~/Filer\")")
        options, offline = m.get("options", []), m.get("offline", [])
        if not (isinstance(options, list) and all(_text(o) for o in options)):
            raise RuntimeError(f"config.toml {label}: options must be a list of strings")
        if kind == "sshfs" and any("," in o or o.startswith("-") for o in options):
            raise RuntimeError(f"config.toml {label}: sshfs options are -o names like \"cache_timeout=60\"")
        if not (isinstance(offline, list) and all(_text(o) for o in offline)):
            raise RuntimeError(f"config.toml {label}: offline must be a list of folder names")
        if offline and kind != "rclone":
            raise RuntimeError(f"config.toml {label}: offline folders need type = \"rclone\" (sshfs has no cache)")
        full = home.rstrip("/") + path[1:]
        if name in names or full in paths:
            raise RuntimeError(f"config.toml {label}: name and path must be unique")
        names.add(name)
        paths.add(full)
        result.append({"name": name, "type": kind, "source": source, "path": full,
                       "options": list(options), "offline": [o.strip("/") for o in offline]})
    return result


def env_file(mount: dict) -> str:
    """Bash-sourced settings for t2-mount (every value shell-quoted)."""
    q = shlex.quote
    return ("# Managed by t2-mac-kde from config.toml [[mounts]]; edit the config, not this file.\n"
            f"TYPE={q(mount['type'])}\n"
            f"SOURCE={q(mount['source'])}\n"
            f"MOUNTPOINT={q(mount['path'])}\n"
            f"OPTIONS=({' '.join(q(o) for o in mount['options'])})\n"
            f"OFFLINE_FOLDERS={q(chr(10).join(mount['offline']))}\n")
