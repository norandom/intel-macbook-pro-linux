"""Remove only the managed Bash initialization; retain nvm and user data."""
import os
from pathlib import Path
import pwd

from pyinfra.operations import files
from manage.node import BASH_MARKER
from manage.preflight import validate_local_context

validate_local_context()
home = Path(pwd.getpwuid(os.getuid()).pw_dir)
files.block(
    name='Remove managed nvm Bash initialization',
    path=str(home / '.bashrc'),
    marker=BASH_MARKER,
    present=False,
    backup=True,
)
