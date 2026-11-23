"""Applications (port of source tasks/apps.py + terminator/xfe/htop bits of desktop.py).

Run: .venv/bin/pyinfra @local tasks/apps.py [--dry]

- Native Ubuntu packages through the foundation guard (no vendor repos, no .debs).
- Pinned upstream release binaries into ~/.local/bin (sha256 verified, user-level).
- Source desktop entries + seed-once htop/Xfe configs (existing user files are kept).
- Availability report: ~/.local/state/t2-mac-kde/applications.json.
Inventory and dispositions: manage/applications.py. Nothing is removed (no source host-role removal branches).
"""
import os

from pyinfra import host, local, logger
from pyinfra.facts.files import File
from pyinfra.operations import files, python, server

from manage.applications import native_packages, release_tools, write_report
from manage.nix_tools import tools as nix_tools
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
local.include("tasks/package_policy.py")

home = os.path.expanduser("~")
bin_dir = f"{home}/.local/bin"
marks = f"{home}/.local/share/t2-mac-kde/release-tools"
# Tools in config nix_tools come from the Nix profile (tasks/nix_tools.py), not from here.
nix_attrs = nix_tools(setting("nix_tools"))

install_packages(PackageRequest(packages=native_packages(), source="ubuntu"))

# Ubuntu names it fdfind; tools look for fd. User-owned link, only if nothing is there.
fd = f"{bin_dir}/fd"
server.shell(
    name="fd -> fdfind (~/.local/bin, only if absent)",
    commands=[f'[ -e "{fd}" ] || [ -L "{fd}" ] || ! [ -x /usr/bin/fdfind ] || '
              f'{{ mkdir -p "{bin_dir}" && ln -s /usr/bin/fdfind "{fd}"; }}'],
)

# --- Release binaries (source release_tools minus what Nix provides; podman-tui: rootless-containers) ---
for name, (version, url, sha) in release_tools(nix_attrs).items():
    dest, mark = f"{bin_dir}/{name}", f"{marks}/{name}.sha256"
    if host.get_fact(File, path=dest) and not host.get_fact(File, path=mark):
        logger.warning(f"apps: {dest} exists and is not managed here; leaving it alone ({name} {version} skipped)")
        continue
    archive = url.rsplit("/", 1)[1]
    server.shell(
        name=f"{name} {version} -> ~/.local/bin (sha256 verified)",
        commands=[f"""[ -x "{dest}" ] && [ "$(cat "{mark}" 2>/dev/null)" = "{sha}" ] || (set -eu
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
curl -fsSL --proto '=https' --tlsv1.2 -o "$t/{archive}" "{url}"
echo "{sha}  $t/{archive}" | sha256sum -c --quiet
mkdir "$t/x"
case "{archive}" in
  *.zip) unzip -q "$t/{archive}" -d "$t/x" ;;
  *.tar|*.tar.*|*.tgz) tar --no-same-owner -xf "$t/{archive}" -C "$t/x" ;;
  *) cp "$t/{archive}" "$t/x/{name}" ;;
esac
found=$(find "$t/x" -type f -name "{name}")
[ "$(printf '%s\\n' "$found" | grep -c .)" = 1 ] || {{ echo "{name}: expected exactly one '{name}' in {archive}" >&2; exit 1; }}
mkdir -p "{bin_dir}" "{marks}"
install -m 755 "$found" "{dest}.new" && mv -f "{dest}.new" "{dest}"
echo "{sha}" > "{mark}")"""],
    )

# --- VLC: E-AC-3 (DDP5.1, most WEB-DL video) has no sound otherwise -------------------------
# VLC's S/PDIF passthrough module grabs E-AC-3 first, PipeWire's Pulse sink refuses the stream
# ("too low audio sample frequency (0)", "failed to create audio output"); --no-spdif does not
# help. Decoding with libavcodec first does. One key; VLC keeps the rest of its vlcrc.
files.directory(name="~/.config/vlc", path=f"{home}/.config/vlc", mode="700")
files.line(name="VLC: decode with libavcodec first (E-AC-3 sound)", path=f"{home}/.config/vlc/vlcrc",
           line=r"^#?codec=.*", replace="codec=avcodec,any")

# --- Desktop entries (source files/applications; hypr-licenses is private data, not ported) ---
for entry in ("x3270", "nedit", "foot-server", "footclient"):
    files.put(name=f"Desktop entry: {entry}", src=f"files/applications/{entry}.desktop",
              dest=f"{home}/.local/share/applications/{entry}.desktop", mode="644", create_remote_dir=True)
# Source terminator.desktop launches hypr-term (coordinated-themes); without it keep Ubuntu's entry.
if host.get_fact(File, path="/usr/local/bin/hypr-term"):
    files.put(name="Desktop entry: terminator (via hypr-term)", src="files/applications/terminator.desktop",
              dest=f"{home}/.local/share/applications/terminator.desktop", mode="644", create_remote_dir=True)
else:
    logger.info("apps: /usr/local/bin/hypr-term absent; terminator.desktop override skipped")
# Deckle (installed by hand): its .deb entry disables WebKit's DMA-BUF renderer; typing lags.
if host.get_fact(File, path="/usr/bin/Deckle"):
    files.put(name="Desktop entry: Deckle (WebKit DMA-BUF renderer on)", src="files/applications/Deckle.desktop",
              dest=f"{home}/.local/share/applications/Deckle.desktop", mode="644", create_remote_dir=True)

# --- Seed-once configs (the apps rewrite these files; never overwrite the user's) ---
# (Xfe seed not ported: xfe is blocked, see manage/applications.py.)
for src, dest in (("files/htop/htoprc", ".config/htop/htoprc"),):
    if not host.get_fact(File, path=f"{home}/{dest}"):
        files.put(name=f"Seed ~/{dest}", src=src, dest=f"{home}/{dest}", mode="644", create_remote_dir=True)

# Owner preference from the source repo: process lists sorted by memory. Only these keys are
# enforced (htop/btop rewrite the rest of their files themselves).
for path, line, replace in (
    (".config/htop/htoprc", r"^sort_key=.*", "sort_key=47"),             # 47 = PERCENT_MEM
    (".config/htop/htoprc", r"^sort_direction=.*", "sort_direction=-1"),  # descending
    (".config/btop/btop.conf", r"^proc_sorting = .*", 'proc_sorting = "memory"'),
):
    files.line(name=f"~/{path}: {replace}", path=f"{home}/{path}", line=line, replace=replace,
               ensure_newline=True)

python.call(name="Availability report (~/.local/state/t2-mac-kde/applications.json)",
            function=lambda: logger.info(f"apps: wrote {write_report(home, nix_attrs)}"))
