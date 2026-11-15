"""Per-user nvm and Node/npm; no system packages or npm prefix override."""
import os
import re
from pathlib import Path
from shlex import quote

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

if os.geteuid() == 0:
    raise RuntimeError("Run pyinfra as your desktop user, not via sudo.")

home = Path.home()
version = (Path(__file__).resolve().parent.parent / ".nvmrc").read_text().strip()
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise ValueError(".nvmrc must contain an exact Node version (major.minor.patch)")
nvm_version = "0.41.0"
env = f"export NVM_DIR={quote(str(home / '.nvm'))}; "
load = env + '. "$NVM_DIR/nvm.sh" --no-use; '

def missing(check):
    """Evaluate after earlier operations, so a first install works in one run."""
    return lambda: host.get_fact(
        Command, command="bash -c " + quote(f"({check}) >/dev/null 2>&1 && echo yes || echo no")
    ) != "yes"


server.shell(
    name=f"Install nvm {nvm_version} for the desktop user",
    commands=env + f"""set -e
installer=$(mktemp)
trap 'rm -f "$installer"' EXIT
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v{nvm_version}/install.sh -o "$installer"
PROFILE=/dev/null bash "$installer"
""",
    _shell_executable="bash",
    _if=missing(load + f'[ "$(nvm --version)" = "{nvm_version}" ]'),
)
server.shell(
    name=f"Install Node {version} with bundled npm and npx",
    commands=load + f"nvm install {version}",
    _shell_executable="bash",
    _if=missing(load + f'[ "$(nvm version {version})" = "v{version}" ]'),
)
server.shell(
    name=f"Default Node version: {version}",
    commands=load + f"nvm alias default {version}",
    _shell_executable="bash",
    _if=missing(load + f'[ "$(nvm version default)" = "v{version}" ]'),
)
files.block(
    name="Load nvm and user tools in Bash",
    path=str(home / ".bashrc"),
    marker="# {mark} t2-mac-kde developer tools",
    content='export PATH="$HOME/.local/bin:$PATH"\n'
            'export NVM_DIR="$HOME/.nvm"\n'
            '[ ! -s "$NVM_DIR/nvm.sh" ] || . "$NVM_DIR/nvm.sh"',
)
