"""Xfe file manager (owner's classic X apps) without removing KDE's im-config.

See manage/xfe.py. Its themes and libfox come from apt normally; the user seed
config (Windows 3.11 colours) is placed by tasks/desktop.py.
"""
from pathlib import Path
import shlex

from pyinfra.operations import server
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage import xfe

validate_local_context()
install_packages(PackageRequest(packages=("libfox-1.6-0", "xfe-themes")))
if not xfe.installed():
    project = Path(__file__).resolve().parents[1]
    server.shell(name=f"Xfe {xfe.VERSION} into /usr/local (verified Ubuntu archive, im-config kept)",
                 commands=f"cd {shlex.quote(str(project))} && /usr/bin/python3 -m manage.xfe --apply", _sudo=True)
