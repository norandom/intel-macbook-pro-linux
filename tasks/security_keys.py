"""Security keys: YubiKey tools, and (config yubikey_login) touch-the-key instead of a password.

    .venv/bin/pyinfra @local tasks/security_keys.py --use-sudo-password

Recommended: two keys, a primary and a spare (docs/security-keys.md). Always: yubikey-manager
(ykman), pam_u2f, pcscd, and `t2-yubikey` to register keys. With yubikey_login = true and at
least one registered key, pam_u2f becomes a sufficient alternative to the password for sudo,
polkit, the login screen and the lock screen; the password keeps working.
"""
import os
from io import StringIO
from pathlib import Path

from pyinfra import logger
from pyinfra.operations import files, server

from manage import security_keys as sk
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
user = os.environ.get("USER") or os.getlogin()
project = Path(__file__).resolve().parents[1]

install_packages(PackageRequest(packages=sk.PACKAGES, source="ubuntu"))
files.put(name="~/.local/bin/t2-yubikey (register | add-spare | status)",
          src=str(project / "files/security-keys/t2-yubikey"),
          dest=os.path.expanduser("~/.local/bin/t2-yubikey"), mode="755", create_remote_dir=True)

on = setting("yubikey_login", False)
if not isinstance(on, bool):
    raise ValueError("yubikey_login must be true or false")
staged = Path(os.path.expanduser(sk.STAGED))
lines = sk.mapping_lines(staged.read_text(), user) if staged.is_file() else []

if on and not lines:
    logger.warning("yubikey_login = true but no key registered: run `t2-yubikey register` (and add-spare), "
                   "then deploy again. PAM stays unchanged.")
elif on:
    if sk.key_count(lines[0]) < 2:
        logger.warning("Only one YubiKey registered: add the spare with `t2-yubikey add-spare` "
                       "(the password still works if the key is lost).")
    files.directory(name="/etc/t2-mac-kde", path="/etc/t2-mac-kde", mode="755", _sudo=True)
    files.put(name=f"Key handles -> {sk.MAPPINGS} (root-owned)", src=StringIO("\n".join(lines) + "\n"),
              dest=sk.MAPPINGS, mode="644", user="root", group="root", _sudo=True)
    files.put(name="pam-auth-update profile t2-u2f", src=StringIO(sk.profile()), dest=sk.PROFILE,
              mode="644", _sudo=True)
    server.shell(name="Enable pam_u2f (sudo, polkit, login, lock screen; password keeps working)", _sudo=True,
                 commands=[f"grep -q pam_u2f /etc/pam.d/common-auth || "
                           f"DEBIAN_FRONTEND=noninteractive pam-auth-update --enable {sk.PROFILE_NAME}"])
else:
    server.shell(name="pam_u2f login off (yubikey_login = false)", _sudo=True, commands=[
        f"[ ! -e {sk.PROFILE} ] || {{ DEBIAN_FRONTEND=noninteractive pam-auth-update --disable {sk.PROFILE_NAME} "
        f"&& rm -f {sk.PROFILE}; }}"])
