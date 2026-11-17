"""Preserve Warpeer preferences while applying managed terminal settings."""
import re
import tomllib


def _string_setting(text: str, table: str, key: str, value: str) -> str:
    parsed = tomllib.loads(text)
    current = parsed
    for part in table.split('.'):
        current = current.get(part, {})
    if current.get(key) == value:
        return text
    assignment = f'{key} = "{value}"'
    section = re.search(r'^\[' + re.escape(table) + r'\][ \t]*(?:#.*)?$', text, re.M)
    if section:
        end = re.search(r'^\[', text[section.end():], re.M)
        stop = section.end() + end.start() if end else len(text)
        body = text[section.end():stop]
        pattern = re.compile(r'^' + re.escape(key) + r'\s*=.*$', re.M)
        body = pattern.sub(assignment, body) if pattern.search(body) else '\n' + assignment + body
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
