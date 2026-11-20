"""[default_apps] in config.toml: MIME type = desktop file id, checked before anything runs."""
import re

_MIME = re.compile(r"[a-z0-9][a-z0-9.+-]*/[A-Za-z0-9][A-Za-z0-9.+_-]*\Z")
_DESKTOP = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.desktop\Z")


def entries(table) -> list[tuple[str, str]]:
    if not isinstance(table, dict):
        raise RuntimeError("config.toml: [default_apps] must be a table of MIME type = desktop file")
    bad = [f"{k} = {v!r}" for k, v in table.items()
           if not (isinstance(k, str) and _MIME.match(k) and isinstance(v, str) and _DESKTOP.match(v))]
    if bad:
        raise RuntimeError("config.toml [default_apps]: not 'type/subtype = \"app.desktop\"': " + ", ".join(bad)
                           + ". A plain setting placed after [default_apps] belongs above that table.")
    return sorted(table.items())
