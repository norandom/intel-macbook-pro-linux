"""Preserve Warpeer preferences while applying managed terminal settings."""
import json
import re
import tomllib


def _literal_setting(text: str, table: str, key: str, literal: str) -> str:
    value = tomllib.loads(f"value = {literal}")["value"]
    parsed = tomllib.loads(text)
    current = parsed
    for part in table.split('.'):
        current = current.get(part, {})
    if current.get(key) == value:
        return text
    assignment = f'{key} = {literal}'
    section = re.search(r'^\[' + re.escape(table) + r'\][ \t]*(?:#.*)?$', text, re.M)
    if section:
        end = re.search(r'^\[', text[section.end():], re.M)
        stop = section.end() + end.start() if end else len(text)
        body = text[section.end():stop]
        pattern = re.compile(r'^' + re.escape(key) + r'\s*=.*$', re.M)
        body = pattern.sub(lambda _: assignment, body) if pattern.search(body) else '\n' + assignment + body
        result = text[:section.end()] + body + text[stop:]
    else:
        result = text.rstrip() + f'\n\n[{table}]\n{assignment}\n'
    current = tomllib.loads(result)
    for part in table.split('.'):
        current = current[part]
    assert current[key] == value
    return result


def startup_shell_config(text: str, shell: str) -> str:
    if shell not in ("bash", "fish"):
        raise ValueError("Unsupported managed shell")
    return _string_setting(text, 'session', 'startup_shell_override', shell)


def pinned_input_config(text: str) -> str:
    return _string_setting(text, 'appearance.input', 'input_mode', 'pinned_to_top')


def font_config(text: str, family: str = "Fixedsys Excelsior") -> str:
    if not isinstance(family, str) or not family.strip():
        raise ValueError("warpeer_font must be a nonempty font family")
    for key in ("font_name", "ai_font_name", "ui_font_name"):
        text = _string_setting(text, 'appearance.text', key, family)
    return text


def contrast_config(text: str) -> str:
    """Keep explicit shell RGB colours readable when the terminal theme changes."""
    return _string_setting(text, 'appearance.text', 'enforce_minimum_contrast', 'always')


def _string_setting(text: str, table: str, key: str, value: str) -> str:
    return _literal_setting(text, table, key, json.dumps(value, ensure_ascii=False))


def defaults_config(text: str, defaults: str) -> str:
    """Fill missing preferences from our simple, single-line TOML defaults."""
    tomllib.loads(defaults)
    table = ''
    for line in defaults.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('['):
            table = line[1:-1]
            continue
        key, literal = (part.strip() for part in line.split('=', 1))
        current = tomllib.loads(text)
        for part in table.split('.'):
            current = current.get(part, {})
        if key not in current:
            text = _literal_setting(text, table, key, literal)
    return text


def opaque_config(text: str) -> str:
    text = _literal_setting(text, 'appearance.window', 'override_opacity', '100')
    return _literal_setting(text, 'appearance.window', 'override_blur', '0')
