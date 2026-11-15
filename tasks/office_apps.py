"""Office and creative apps: LibreOffice Writer + Calc (Ubuntu archive, Tabbed UI admin
layer), the ArtCraft suite (storytold/*) and OpenIDEA (l0ng-ai/openidea) as pinned .debs.

Every .deb is downloaded by URL, sha256-checked, then installed through the guarded
root helper (`python -m manage.packages --apply <staged .deb>`: apt simulation without
removals, protected-package check, payload + maintainer-script scan). A package whose
dpkg version already equals the pin is skipped. Bumping a pin: edit VERSION + SHA256
(GitHub shows the asset digest on the release page / `gh api .../releases`).
"""
from pathlib import Path
import subprocess

from pyinfra.operations import files, server
from manage.packages import PackageRequest, install_packages, schedule_batch
from manage.preflight import validate_local_context

# Ubuntu archive: Writer + Calc with the GTK3 (Wayland) UI, German UI pack, de + en-US
# spelling/hyphenation/thesaurus, Carlito (metric-compatible Calibri).
LIBREOFFICE = (
    "libreoffice-calc", "libreoffice-writer", "libreoffice-gtk3", "fonts-crosextra-carlito",
    "libreoffice-l10n-de", "hunspell-de-de", "hunspell-en-us", "hyphen-de", "hyphen-en-us",
    "mythes-de", "mythes-en-us",
)
XCD_DEST = "/usr/lib/libreoffice/share/registry/t2-mac-kde.xcd"

# ArtCraft suite: name -> (version, sha256 of <name>-<ver>-linux-x86_64.deb = GitHub asset digest).
ARTCRAFT = {
    "pdfcraft": ("0.21.1", "e87baa0ef638be6ea97b521883e912318012028a80dbe1359f93cd21437be253"),
    "designcraft": ("0.20.1", "a4b50ceffd33a13d2d52e01530f6de3236d50ada02a7cf0c8946de3195057b0f"),
    "gridcraft": ("0.19.1", "3e9b093ee3bed8b1f008ea56c8d60e6a96890e24317be2bbb93e431f3c9d8112"),
    "lightcraft": ("0.21.1", "c91ef47bec44995d99ce58e6c748af9fa6ab1ff1c11de9e290e0b8231176dad1"),
    "wordcraft": ("0.18.1", "9b557161ded7b5973112c8c21f600fe0b0110c1a4d3151184485733c96f87e19"),
    "deckcraft": ("0.18.1", "59801c24ef5bdaf01a6a465f0e1d5f59aba36ad1e723cb833304b22d98c3f909"),
    "cadcraft": ("0.20.1", "8e6ad1f487d6cd44dbcb73cd88ef1efb52252a2071094f2c23a468a641a06faa"),
}

# OpenIDEA (Apache-2.0): releases are near-daily; bump these two lines by hand.
OPENIDEA_VERSION = "0.1.45"
OPENIDEA_SHA256 = "3583af406fdd008d5c47bc555068a0d541eb9f1e131f2e527b3a5f8b2d4bc003"


def debs() -> dict[str, tuple[str, str, str]]:
    """dpkg package -> (dpkg version, url, sha256) for every pinned .deb."""
    table = {name: (f"{ver}-1", f"https://github.com/storytold/{name}/releases/download/v{ver}/"
                    f"{name}-{ver}-linux-x86_64.deb", sha) for name, (ver, sha) in ARTCRAFT.items()}
    table["open-idea"] = (OPENIDEA_VERSION, "https://github.com/l0ng-ai/openidea/releases/download/"
                          f"v{OPENIDEA_VERSION}/OpenIDEA_{OPENIDEA_VERSION}_amd64.deb", OPENIDEA_SHA256)
    return table


def installed_version(package: str) -> str | None:
    result = subprocess.run(["dpkg-query", "-W", "-f=${Version}", package],
                            capture_output=True, text=True, timeout=10)
    return result.stdout.strip() if result.returncode == 0 else None


validate_local_context()
# One guarded transaction: missing LibreOffice packages + every pinned .deb not at its pin.
missing_lo = tuple(p for p in LIBREOFFICE if installed_version(p) is None)
if missing_lo:
    install_packages(PackageRequest(packages=missing_lo), preview_only=True)  # plan-time guard preview
schedule_batch("Office + Craft + OpenIDEA", packages=missing_lo,
               debs=[(p, v, u, s) for p, (v, u, s) in debs().items() if installed_version(p) != v])
# Tabbed UI (ribbon) for Writer and Calc as the system default: an admin .xcd layer;
# the user's own choice in View > User Interface overrides it.
files.put(name="LibreOffice: Tabbed UI layer", src=str(Path(__file__).resolve().parents[1] / "files/office-apps/t2-mac-kde.xcd"),
          dest=XCD_DEST, user="root", group="root", mode="644", _sudo=True)
