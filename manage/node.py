"""Read-only checks before provisioning the desktop user's nvm installation."""

import os
from pathlib import Path
import re
from collections.abc import Mapping

BASH_MARKER = '# {mark} t2-mac-kde developer tools'
BASH_INIT = '''case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
export NVM_DIR="$HOME/.nvm"
[ ! -s "$NVM_DIR/nvm.sh" ] || . "$NVM_DIR/nvm.sh"'''


def validate_node_config(version: str, home: Path, environment: Mapping[str, str] | None = None) -> str:
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
        raise ValueError('.nvmrc must contain an exact Node version (major.minor.patch)')
    environment = os.environ if environment is None else environment
    expected = {'npm_config_userconfig': str(home / '.npmrc'), 'nvm_dir': str(home / '.nvm')}
    for key, value in environment.items():
        normalized = key.lower()
        if normalized in ('prefix', 'npm_config_prefix', 'npm_config_globalconfig'):
            raise RuntimeError(f'Unset {key} before running the nvm deployment; npm overrides conflict with nvm.')
        if normalized in expected and value != expected[normalized]:
            raise RuntimeError(f'Unset {key} before running the nvm deployment; use the desktop account defaults.')
    config = home / '.npmrc'
    if config.exists():
        try:
            content = config.read_text()
        except (OSError, UnicodeError) as error:
            raise RuntimeError('Cannot inspect ~/.npmrc; fix its permissions/encoding before provisioning.') from error
        for line in content.splitlines():
            setting = line.strip()
            if not setting or setting.startswith(('#', ';')):
                continue
            key = setting.partition('=')[0].strip().lower()
            if key in ('prefix', 'globalconfig'):
                raise RuntimeError(f'Remove the {key} setting from ~/.npmrc before using nvm; the file was preserved.')
    return version


def default_alias_matches(home: Path, version: str) -> bool:
    try:
        return (home / '.nvm/alias/default').read_text().strip() == version
    except FileNotFoundError:
        return False
