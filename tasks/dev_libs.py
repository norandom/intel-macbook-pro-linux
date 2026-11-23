"""Desktop app development: GTK/WebKit build dependencies (Tauri, e.g. the 1-1 RDP client) and
Qt 6 (Qt Creator, C++ headers, QML, CMake/Ninja, PyQt6 and PySide6), all from the Ubuntu archive.

Opt-out with config `dev_libs = false`. The tray library is Ubuntu's Ayatana one
(libayatana-appindicator3-dev, which also provides libappindicator3-dev): the legacy
libappindicator3-dev conflicts with libayatana-appindicator3-1, and installing it removes
nm-applet and 1-1. If the legacy pair is installed, this task replaces it (the only
removal the package guard allows here), so the tray apps can be reinstalled by later tasks.
"""
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting

PACKAGES = ("libwebkit2gtk-4.1-dev", "libayatana-appindicator3-dev", "librsvg2-dev",
            "libdbus-1-dev", "libssl-dev", "pkg-config")
REPLACES = ("libappindicator3-dev", "libappindicator3-1")
# Qt 6: Qt Creator (with clangd/clang-tidy for its code model), headers and tools for C++ and
# QML, CMake + Ninja (Qt Creator's default build), and both Python bindings with their tools
# (pyuic6/pyside6-uic, Designer). Qt Creator's recommends are listed here, since the guard
# installs without recommends.
QT = ("qtcreator", "clang-tidy", "cmake", "ninja-build",
      "qt6-base-dev", "qt6-declarative-dev", "qt6-declarative-dev-tools", "qt6-tools-dev", "qt6-tools-dev-tools",
      "qml-qt6", "qt6-qmltooling-plugins", "qt6-translations-l10n",
      "python3-pyqt6", "pyqt6-dev-tools", "pyside6-tools",
      "python3-pyside6.qtcore", "python3-pyside6.qtgui", "python3-pyside6.qtwidgets", "python3-pyside6.qtnetwork",
      "python3-pyside6.qtqml", "python3-pyside6.qtquick", "python3-pyside6.qtquickcontrols2")

validate_local_context()
if setting("dev_libs", True):
    install_packages(PackageRequest(packages=PACKAGES + QT, replaces=REPLACES))
