"""Preview effective package policy, then schedule its owned system change."""
from pathlib import Path
import shlex

from pyinfra.operations import server

from manage.package_policy import CONTENT, NAME, verify_effective_policy
from manage.preflight import validate_local_context

validate_local_context()
verify_effective_policy(preview=True)
owned = Path("/etc/apt/preferences.d", NAME)
if owned.is_file() and owned.read_bytes() == CONTENT:
    verify_effective_policy()
else:
    server.shell(
        name="Maintain and verify owned Snap/Flatpak prohibition",
        commands='/usr/bin/python3 ' + shlex.quote(str(Path(__file__).resolve().parents[1] / 'manage/package_policy.py')) + ' --apply',
        _sudo=True,
    )
