"""Owner-requested removals (2026-11-23): apps taken out of the inventory, removed if installed.

apt remove, not purge: the apps' own settings in ~ (e.g. ~/.config/remmina) stay.
"""
import subprocess

from pyinfra.operations import apt
from manage.preflight import validate_local_context

REMOVE = {
    # 1-1 is the RDP client
    "Remmina": ("remmina", "remmina-common", "remmina-plugin-rdp", "remmina-plugin-vnc", "remmina-plugin-secret"),
    # Penguin Mail is the mail app; KOrganizer (calendar) stays
    "KMail + Kontact": ("kmail", "kontact", "accountwizard"),
    # Devolutions Remote Desktop Manager (vendor .deb); 1-1 is the RDP client
    "Remote Desktop Manager": ("remotedesktopmanager",),
}

validate_local_context()
for label, packages in REMOVE.items():
    installed = [p for p in packages if subprocess.run(
        ["dpkg-query", "-W", "-f=${db:Status-Status}", p], capture_output=True, text=True).stdout == "installed"]
    if installed:
        apt.packages(name=f"Remove {label} (owner request)", packages=installed, present=False, _sudo=True)
