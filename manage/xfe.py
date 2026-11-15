"""Root helper: unpack Ubuntu's xfe .deb into /usr/local without dpkg.

Ubuntu's xfe declares `Conflicts: im-config` (ibus trouble), and im-config is a
kubuntu-desktop dependency of the dormant KDE base. Unpacking the verified
archive avoids removing it; the /usr/local/bin wrappers clear the input-method
variables, which is what the conflict guards against. No maintainer scripts run.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from manage.packages import check_archive

VERSION = "2.1.1-1"
SHA256 = "8c14d758ada1e5adbd75cfc8c578be254252a7afc54862bdfe7f3cc55ba2ae52"
LIB = Path("/usr/local/lib/xfe")
WRAPPER = '#!/bin/sh\n# t2-mac-kde: run Ubuntu xfe without ibus input-method hooks\n' \
          'unset XMODIFIERS GTK_IM_MODULE QT_IM_MODULE\nexec /usr/local/lib/xfe/bin/"$(basename "$0")" "$@"\n'
ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C", "LANG": "C"}


def installed() -> bool:
    try:
        return (LIB / "VERSION").read_text().strip() == VERSION
    except OSError:
        return False


def apply() -> None:
    if os.geteuid() != 0:
        raise SystemExit("manage.xfe --apply must run as root")
    if installed():
        return
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["apt-get", "download", f"xfe={VERSION}"], cwd=tmp, env=ENV, check=True)
        deb = next(Path(tmp).glob("xfe_*.deb"))
        if hashlib.sha256(deb.read_bytes()).hexdigest() != SHA256:
            raise SystemExit("xfe archive sha256 mismatch")
        check_archive(deb)
        root = Path(tmp, "root")
        subprocess.run(["dpkg-deb", "-x", str(deb), str(root)], env=ENV, check=True)
        if LIB.exists():
            shutil.rmtree(LIB)
        shutil.copytree(root / "usr/bin", LIB / "bin", symlinks=True)
        share = Path("/usr/local/share")
        (share / "xfe").mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / "etc/xfe/xferc", share / "xfe/xferc")
        shutil.copytree(root / "usr/share/icons", share / "icons", dirs_exist_ok=True)
        (share / "applications").mkdir(parents=True, exist_ok=True)
        for desktop in (root / "usr/share/applications").glob("*.desktop"):
            shutil.copy2(desktop, share / "applications" / desktop.name)
        for name in os.listdir(LIB / "bin"):
            wrapper = Path("/usr/local/bin", name)
            wrapper.write_text(WRAPPER)
            wrapper.chmod(0o755)
        (LIB / "VERSION").write_text(VERSION + "\n")


if __name__ == "__main__":
    if sys.argv[1:] != ["--apply"]:
        raise SystemExit("usage: python3 -m manage.xfe --apply")
    apply()
