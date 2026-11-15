"""Per-user settings: ~/.config/t2-mac-kde/config.toml (keeps the repo generic).

Precedence: pyinfra `--data key=value` > config file > the task's default.
Personal values (device MACs, panel quirks, exit node, ...) belong in the file, never
in the repo. See files/config.example.toml for every key.
"""
import os
from pathlib import Path
import tomllib


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return Path(base, "t2-mac-kde", "config.toml")


def load(path: Path | None = None) -> dict:
    path = path or config_path()
    try:
        with open(path, "rb") as stream:
            data = tomllib.load(stream)
    except FileNotFoundError:
        return {}
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise RuntimeError(f"Invalid {path}: {error}") from error
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid {path}: top level must be a table")
    return data


_CACHE: dict | None = None


def setting(key: str, default=None):
    from pyinfra import host
    global _CACHE
    explicit = host.data.get(key)
    if explicit is not None:
        return explicit
    if _CACHE is None:
        _CACHE = load()
    return _CACHE.get(key, default)
