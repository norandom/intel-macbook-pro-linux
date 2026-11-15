"""Public fonts (source tasks/fonts.py, user-level): JetBrainsMono / FiraCode Nerd Fonts,
Fixedsys Core / Excelsior, emoji + Symbola fallback, an additive fontconfig fragment,
a Fixedsys core-font index and the hypr-xfonts session helper.

    .venv/bin/pyinfra @local tasks/fonts.py --dry
    .venv/bin/pyinfra @local tasks/fonts.py [--data font_rendering=rgb]
"""
import logging
import os

from pyinfra import host
from pyinfra.operations import files, server

from manage.preflight import validate_local_context
from manage.packages import PackageRequest, install_packages
from manage import fonts as F

validate_local_context()
F.validate_manifest()

rendering = host.data.get("font_rendering", "grayscale")
if rendering not in F.RENDERING_MODES:
    raise ValueError(f"font_rendering must be one of {F.RENDERING_MODES}, not {rendering!r}")

home = os.path.expanduser("~")
P = F.paths(home)

install_packages(PackageRequest(packages=F.PACKAGES, source="ubuntu"))

for family in F.NERD_FONTS:
    dest = F.nerd_dest(P["fonts"], family)
    if not F.nerd_installed(dest, family):
        server.shell(
            name=f"{family} Nerd Font {F.NERD_VERSION} -> {dest} (sha256 verified)",
            commands=[F.nerd_script(family, dest)],
        )

for name, (_url, sha) in F.EXTRA_FONTS.items():
    if F.sha256(P["extra"] / name) != sha:
        server.shell(
            name=f"Font {name} -> {P['extra']} (sha256 verified)",
            commands=[F.extra_script(name, P["extra"])],
        )

# Fixedsys as core X fonts (NEdit etc.): own indexed directory, added to
# Xwayland's font path by hypr-xfonts at session start.
if not F.core_index_ok(P["core"]):
    server.shell(
        name=f"Fixedsys core X font index (mkfontscale/mkfontdir) -> {P['core']}",
        commands=[F.core_script(P["extra"], P["core"])],
    )

files.put(
    name=f"hypr-xfonts helper -> {P['helper']}",
    src="files/fonts/hypr-xfonts",
    dest=str(P["helper"]),
    mode="755",
)

# Additive fragment only; ~/.config/fontconfig/fonts.conf (KDE writes it) is never
# touched and is loaded after conf.d, so its rules keep precedence.
files.directory(name="fontconfig conf.d", path=str(P["fragment"].parent), present=True)
files.template(
    name=f"fontconfig fragment: hintslight, {rendering} AA, monospace = JetBrainsMono Nerd Font",
    src="templates/fontconfig/60-t2-fonts.conf.j2",
    dest=str(P["fragment"]),
    mode="644",
    font_rendering=rendering,
)

conflicts = F.user_conf_conflicts(P["user_conf"])
if conflicts:
    logging.getLogger("pyinfra").warning(
        "%s sets %s; those user settings override the managed fragment (left untouched).",
        P["user_conf"], ", ".join(conflicts))
