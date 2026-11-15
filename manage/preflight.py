"""Read-only checks for the desktop-user deployment context."""

import os
import platform

from pyinfra import host
from pyinfra.connectors import util as _connector_util
from pyinfra.connectors.local import LocalConnector

# sudo-rs 0.2.x prints "sudo: interactive authentication is required", but
# pyinfra 3.10 only retries with a password on the "sudo-rs:" spelling.
# Without this, --use-sudo-password fails instead of prompting.
_SUDO_RS_LINE = "sudo: interactive authentication is required"
if _SUDO_RS_LINE not in _connector_util.SUDO_PASSWORD_REQUIRED_LINES:
    _connector_util.SUDO_PASSWORD_REQUIRED_LINES += (_SUDO_RS_LINE,)


def validate_local_context() -> None:
    """Require an unprivileged local Ubuntu context before scheduling changes."""
    if platform.system() != "Linux":
        raise RuntimeError("Unsupported operating system: run this deployment on Ubuntu Linux.")

    if os.getuid() == 0 or os.geteuid() == 0:
        raise RuntimeError("Run pyinfra as your desktop user, not via sudo or a root shell.")

    # A hostname such as localhost is still SSH; check the actual connector.
    # Checking the whole inventory also blocks a mixed local/remote deploy
    # before its local portion can schedule operations.
    if getattr(host, "connector_cls", None) is not LocalConnector:
        raise RuntimeError("Use only the @local pyinfra inventory for this workstation deployment.")
    targets = tuple(host.inventory)
    if len(targets) != 1 or targets[0].connector_cls is not LocalConnector:
        raise RuntimeError("Use only the @local pyinfra inventory; mixed or remote targets are unsupported.")

    try:
        release = platform.freedesktop_os_release()
    except OSError as error:
        raise RuntimeError("Cannot verify local Ubuntu identity; check the local os-release file.") from error
    if release.get("ID") != "ubuntu":
        raise RuntimeError("Unsupported operating system: native Ubuntu is required.")
