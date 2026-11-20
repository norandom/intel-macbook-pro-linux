"""Build dependencies for GTK/WebKit desktop apps (Tauri: e.g. the 1-1 RDP client).

Opt-out with config `dev_libs = false`. The tray library is Ubuntu's Ayatana one
(libayatana-appindicator3-dev, which also provides libappindicator3-dev): the legacy
libappindicator3-dev conflicts with libayatana-appindicator3-1, and installing it removes
nm-applet, Remmina and 1-1. If the legacy pair is installed, this task replaces it (the only
removal the package guard allows here), so the tray apps can be reinstalled by later tasks.
"""
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting

PACKAGES = ("libwebkit2gtk-4.1-dev", "libayatana-appindicator3-dev", "librsvg2-dev",
            "libdbus-1-dev", "libssl-dev", "pkg-config")
REPLACES = ("libappindicator3-dev", "libappindicator3-1")

validate_local_context()
if setting("dev_libs", True):
    install_packages(PackageRequest(packages=PACKAGES, replaces=REPLACES))
