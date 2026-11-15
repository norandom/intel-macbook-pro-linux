"""Per-user nvm and Node/npm; no system packages or npm prefix override."""
import os
import pwd
from pathlib import Path
from shlex import quote

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server
from manage.node import BASH_INIT, BASH_MARKER, default_alias_matches, validate_node_config
from manage.preflight import validate_local_context

validate_local_context()

home = Path(pwd.getpwuid(os.getuid()).pw_dir)
if Path.home() != home:
    raise RuntimeError('HOME must match the local desktop account before provisioning nvm.')
version = (Path(__file__).resolve().parent.parent / ".nvmrc").read_text().strip()
validate_node_config(version, home)
nvm_version = "0.41.0"
env = f"export NVM_DIR={quote(str(home / '.nvm'))}; "
load = env + '. "$NVM_DIR/nvm.sh" --no-use; '
runtime = home / '.nvm' / 'versions' / 'node' / ('v' + version) / 'bin'
executables = ' && '.join(f'test -x {quote(str(runtime / tool))}' for tool in ('node', 'npm', 'npx'))

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
    commands=load + f"nvm install {version} && {executables}",
    _shell_executable="bash",
    _if=missing(load + f'[ "$(nvm version {version})" = "v{version}" ] && {executables}'),
)
server.shell(
    name=f"Default Node version: {version}",
    commands=load + f"nvm alias default {version}",
    _shell_executable="bash",
    _if=lambda: not default_alias_matches(home, version),
)
files.block(
    name="Load nvm and user tools in Bash",
    path=str(home / ".bashrc"),
    marker=BASH_MARKER,
    content=BASH_INIT,
    backup=True,
)
