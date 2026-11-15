#!/bin/sh
# Bootstrap only uv and the project environment; system changes use pyinfra.
set -eu

fail() {
    printf 'bootstrap: %s\n' "$*" >&2
    exit 1
}

cd "$(dirname "$0")"
project_root=$(pwd -P)
command -v python3 >/dev/null 2>&1 || fail 'Python 3.11 or newer is required (python3).'
python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' || fail 'Python 3.11 or newer is required.'
command -v curl >/dev/null 2>&1 || fail 'curl is required; install prerequisites explicitly before retrying.'

# Validate paths before installing anything. uv discovers ancestor workspaces,
# which would otherwise select a different lock and environment even with --project.
python3 - "$project_root" <<'PY' || exit 1
from pathlib import Path
import sys
import tomllib

root = Path(sys.argv[1])
try:
    for name in ('pyproject.toml', 'uv.lock'):
        if not (root / name).is_file():
            raise ValueError(f'required project file is missing: {name}')
    environment = root / '.venv'
    if environment.is_symlink():
        raise ValueError('project .venv must not be a symlink')
    if environment.exists() and not environment.is_dir():
        raise ValueError('project .venv must be a directory')
    config = environment / 'pyvenv.cfg'
    if config.exists():
        for line in config.read_text().splitlines():
            key, _, value = line.partition('=')
            if key.strip() == 'include-system-site-packages' and value.strip().lower() != 'false':
                raise ValueError('project .venv must exclude system site packages')
    for directory in (root, *root.parents):
        declaration = directory / 'pyproject.toml'
        if declaration.is_file():
            with declaration.open('rb') as source:
                settings = tomllib.load(source)
            if 'workspace' in settings.get('tool', {}).get('uv', {}):
                raise ValueError(f'workspace discovery would escape the standalone project: {directory}')
except (OSError, ValueError) as error:
    print(f'bootstrap: {error}', file=sys.stderr)
    sys.exit(1)
PY

# Ignore inherited project/interpreter/config redirections. Index and offline
# settings remain available; the interpreter and destination are explicit.
unset UV_PROJECT UV_WORKING_DIR UV_CONFIG_FILE UV_FROZEN UV_PYTHON UV_MANAGED_PYTHON
unset UV_UNMANAGED_INSTALL
export UV_PROJECT_ENVIRONMENT="$project_root/.venv"
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
    installer=$(mktemp) || fail 'could not create temporary installer.'
    trap 'rm -f "$installer"' EXIT
    trap 'exit 1' HUP INT TERM
    if ! curl --fail --location --silent --show-error --proto '=https' --proto-redir '=https' \
        https://astral.sh/uv/0.13.8/install.sh -o "$installer"; then
        fail 'uv installer download failed.'
    fi
    if ! UV_NO_MODIFY_PATH=1 UV_INSTALL_DIR="$HOME/.local/bin" sh "$installer"; then
        fail 'uv installation failed.'
    fi
fi

uv --version || fail 'could not run uv.'
python_path=$(python3 -c 'import sys; print(sys.executable)')
if ! uv sync --locked --no-config --directory "$project_root" --project "$project_root" \
    --python "$python_path" --no-python-downloads; then
    fail 'locked project environment sync failed.'
fi
