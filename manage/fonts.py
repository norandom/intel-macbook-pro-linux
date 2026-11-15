"""Public font pins (source a1c09ec group_data/all.py) and plan-time state checks.

Pure helpers so tasks/fonts.py and tests share one definition. User-level install:
everything lives under the desktop user's home, no sudo.
"""

import hashlib
import os
import re
from pathlib import Path

NERD_VERSION = "3.5.1"
NERD_URL = "https://github.com/ryanoasis/nerd-fonts/releases/download/v{ver}/{family}.tar.xz"
# family -> (sha256 of {family}.tar.xz, styles installed as {family}NerdFont-{style}.ttf)
NERD_FONTS = {
    "JetBrainsMono": ("04d5e8f903693f9dd13e16f867e994834e681eb3c72c0d337a770dcda09010cf",
                      ("Regular", "Bold", "Italic", "BoldItalic")),
    "FiraCode": ("68e3bd6164864b8b514605bc34e3a87ac401c8c48682fcce6478c70263340207",
                 ("Light", "Regular", "Retina", "Medium", "SemiBold", "Bold")),
}
# Single-file public fonts: file name -> (url, sha256). Both go to the core-font index.
EXTRA_FONTS = {
    "FixedsysCore-Regular.ttf": (
        "https://raw.githubusercontent.com/delinx/Fixedsys-Core/"
        "cf4b8e99b1e7a357d7cbe5225323d8413b20f611/FixedsysCore-Regular.ttf",
        "43941ca11fc5bb5650d27c70c673bf629ec1491b9695b1b4e8dacc99713509bd"),
    "FSEX302.ttf": (
        "https://github.com/kika/fixedsys/releases/download/v3.09.10/FSEX302.ttf",
        "842f8fbf80f57d867aeb1d2988140d3ea8b4718e5f687035b0a3b66756df3899"),
}
RENDERING_MODES = ("grayscale", "rgb")
PACKAGES = ("curl", "ca-certificates", "xz-utils", "fontconfig", "xfonts-utils",
            "x11-xserver-utils", "fonts-noto-color-emoji", "fonts-symbola")

_SHA = re.compile(r"^[0-9a-f]{64}$")
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def validate_manifest() -> None:
    for family, (sha, styles) in NERD_FONTS.items():
        if not (_SHA.match(sha) and _NAME.match(family) and styles
                and all(_NAME.match(s) for s in styles)):
            raise ValueError(f"Invalid Nerd Font pin: {family}")
    for name, (url, sha) in EXTRA_FONTS.items():
        if not (_SHA.match(sha) and _NAME.match(name) and url.startswith("https://")):
            raise ValueError(f"Invalid font pin: {name}")


def paths(home: str) -> dict[str, Path]:
    h = Path(home)
    config = Path(os.environ.get("XDG_CONFIG_HOME") or h / ".config")
    return {
        "fonts": h / ".local/share/fonts",
        "extra": h / ".local/share/fonts/fixedsys",
        # Outside ~/.local/share/fonts so fontconfig does not index duplicates.
        "core": h / ".local/share/fonts-x11core",
        "helper": h / ".local/bin/hypr-xfonts",
        "fragment": config / "fontconfig/conf.d/60-t2-fonts.conf",
        "user_conf": config / "fontconfig/fonts.conf",
    }


def nerd_dest(fonts_dir: Path, family: str) -> Path:
    return fonts_dir / f"{family.lower()}-nerd"


def nerd_files(family: str) -> tuple[str, ...]:
    return tuple(f"{family}NerdFont-{s}.ttf" for s in NERD_FONTS[family][1])


def sha256(path: Path) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.file_digest(f, "sha256").hexdigest()
    except OSError:
        return None


def nerd_installed(dest: Path, family: str) -> bool:
    """Version marker AND recorded digests of every selected file still match."""
    if not (dest / f".v{NERD_VERSION}").is_file():
        return False
    try:
        recorded = dict(line.split()[::-1] for line in
                        (dest / ".sha256sums").read_text().splitlines() if line.strip())
    except (OSError, ValueError):
        return False
    return all(name in recorded and sha256(dest / name) == recorded[name]
               for name in nerd_files(family))


def core_index_ok(core: Path) -> bool:
    for name, (_url, sha) in EXTRA_FONTS.items():
        if sha256(core / name) != sha:
            return False
    try:
        index = (core / "fonts.dir").read_text()
    except OSError:
        return False
    return all(name in index for name in EXTRA_FONTS)


def nerd_script(family: str, dest: Path) -> str:
    sha = NERD_FONTS[family][0]
    names = " ".join(nerd_files(family))
    url = NERD_URL.format(ver=NERD_VERSION, family=family)
    # Stage + verify everything, then swap directories: a failure leaves the old family.
    return f"""set -eu
t=$(mktemp -d); trap 'rm -rf "$t" "{dest}.new"' EXIT
curl -fsSL --retry 3 -o "$t/f.tar.xz" {url}
echo "{sha}  $t/f.tar.xz" | sha256sum -c --quiet
mkdir "$t/x"; tar -xJf "$t/f.tar.xz" -C "$t/x" --no-same-owner {names}
rm -rf "{dest}.new"; mkdir -p "{dest}.new"
for f in {names}; do [ -f "$t/x/$f" ] && [ ! -L "$t/x/$f" ]; install -m 644 "$t/x/$f" "{dest}.new/$f"; done
(cd "{dest}.new" && sha256sum {names} > .sha256sums && touch .v{NERD_VERSION})
rm -rf "{dest}.old"; [ ! -e "{dest}" ] || mv "{dest}" "{dest}.old"
mv "{dest}.new" "{dest}"; rm -rf "{dest}.old"
fc-cache -f "{dest}" >/dev/null"""


def extra_script(name: str, dest_dir: Path) -> str:
    url, sha = EXTRA_FONTS[name]
    dest = dest_dir / name
    return f"""set -eu
mkdir -p "{dest_dir}"; trap 'rm -f "{dest}.tmp"' EXIT
curl -fsSL --retry 3 -o "{dest}.tmp" {url}
echo "{sha}  {dest}.tmp" | sha256sum -c --quiet
chmod 644 "{dest}.tmp"; mv "{dest}.tmp" "{dest}"
fc-cache -f "{dest_dir}" >/dev/null"""


def core_script(extra: Path, core: Path) -> str:
    names = " ".join(EXTRA_FONTS)
    return f"""set -eu
rm -rf "{core}.new"; mkdir -p "{core}.new"; trap 'rm -rf "{core}.new"' EXIT
for f in {names}; do install -m 644 "{extra}/$f" "{core}.new/$f"; done
cd "{core}.new"; mkfontscale; mkfontdir
for f in {names}; do grep -q "^$f " fonts.dir; done
chmod 644 fonts.scale fonts.dir; cd /
rm -rf "{core}.old"; [ ! -e "{core}" ] || mv "{core}" "{core}.old"
mv "{core}.new" "{core}"; rm -rf "{core}.old"
"""


def user_conf_conflicts(user_conf: Path) -> list[str]:
    """Rendering/family settings in the user's own fonts.conf (it wins over our fragment)."""
    try:
        text = user_conf.read_text()
    except OSError:
        return []
    keys = ("antialias", "hintstyle", "hinting", "rgba", "lcdfilter", "monospace")
    return [k for k in keys if k in text]
