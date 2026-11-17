"""Shell and user developer tools (shell-user-tools), ported from debian-hypr
tasks/shell.py + tasks/user_tools.py.

grml-inspired Bash, shared history, readline prefix search, completions,
nvim-simple (pinned), npm globals under the foundation nvm Node, euporie via uv,
pretty-mermaid skill, optional rclone mounts / dev-disk-reclaim timer.
Run after tasks/node.py (needs nvm Node) and tasks/tools.py (neovim, git, curl).
"""
import os
import pwd
import shutil
from io import StringIO
from pathlib import Path
from shlex import quote

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, python, server, systemd

from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage import fish_shell
from manage import starship as starship_cfg
from manage import shell_tools as cfg
from manage.userconfig import setting

validate_local_context()
cfg.validate_mounts(cfg.RCLONE_MOUNTS)

repo = Path(__file__).resolve().parent.parent
home = Path(pwd.getpwuid(os.getuid()).pw_dir)
if Path.home() != home:
    raise RuntimeError('HOME must match the local desktop account.')
src = repo / 'files' / 'shell'
bash_dir = home / '.config' / 'bash'
bin_dir = home / '.local' / 'bin'
state_dir = home / '.local' / 'state' / 't2-mac-kde'
units = home / '.config' / 'systemd' / 'user'
node = (repo / '.nvmrc').read_text().strip()
nvm = f'export NVM_DIR={quote(str(home / ".nvm"))}; . "$NVM_DIR/nvm.sh" --no-use && nvm use --silent {node} >/dev/null; '
path = f'export PATH={quote(str(bin_dir))}:"$PATH"; '


def missing(check):
    """True when `check` fails; evaluated at execution time (after earlier ops)."""
    return lambda: host.get_fact(
        Command, command="bash -c " + quote(f"({check}) >/dev/null 2>&1 && echo yes || echo no")
    ) != "yes"


# --- Bash: grml prompt/aliases/dir stack, Kali-style history, readline --------------------
install_packages(PackageRequest(packages=("bash-completion",), source="ubuntu"))

for name in ("grml.bash", "history.bash", "readline.inputrc"):
    files.put(name=f"bash: ~/.config/bash/{name}", src=str(src / name), dest=str(bash_dir / name), mode="644")

files.block(
    name="readline: include /etc/inputrc + prefix history search (marked block in ~/.inputrc)",
    path=str(home / ".inputrc"),
    marker=cfg.INPUTRC_MARKER,
    content=cfg.INPUTRC_INIT,
    try_prevent_shell_expansion=True,
    backup=True,
)

# --- Neovim: nvim-simple (CUA keys, menu bar, Berg theme), pinned plugins --------------
pins = " ".join(quote(f"{r}={c}") for r, c in cfg.NVIM_PLUGINS.items())
stamp = f"{cfg.NVIM_SIMPLE_COMMIT} " + " ".join(f"{r}={c}" for r, c in cfg.NVIM_PLUGINS.items())
server.shell(
    name=f"nvim: nvim-simple {cfg.NVIM_SIMPLE_COMMIT[:7]} with pinned plugins (staged + verified)",
    commands=f"bash {quote(str(src / 'nvim-simple.sh'))} {cfg.NVIM_SIMPLE_COMMIT} {pins}",
    _shell_executable="bash",
    _if=missing(f'[ "$(cat {quote(str(home / ".config/nvim/.nvim-simple"))})" = {quote(stamp)} ]'),
)

# --- npm globals under the foundation nvm Node (no ~/.npmrc prefix) ----------------------
prefix_ok = f'[ "$(npm prefix -g)" = {quote(str(home / ".nvm/versions/node" / ("v" + node)))} ]'
for package, version in cfg.NPM_TOOLS.items():
    server.shell(
        name=f"npm global {package}@{version} (nvm Node {node})",
        commands=nvm + prefix_ok + f" && npm install -g --no-fund --no-audit {quote(f'{package}@{version}')}",
        _shell_executable="bash",
        _if=missing(nvm + f"npm ls -g --depth=0 {quote(f'{package}@{version}')}"),
    )

# Aikido Safe Chain (config safe_chain): pinned npm global; aliases come from the devtools block.
safe_chain = bool(setting("safe_chain", False))
if safe_chain:
    package, version = cfg.SAFE_CHAIN
    server.shell(
        name=f"npm global {package}@{version} (Safe Chain, nvm Node {node})",
        commands=nvm + prefix_ok + f" && npm install -g --no-fund --no-audit {quote(f'{package}@{version}')}",
        _shell_executable="bash",
        _if=missing(nvm + f"npm ls -g --depth=0 {quote(f'{package}@{version}')}"),
    )

server.shell(
    name="Claude Code skill: pretty-mermaid (pinned skills CLI)",
    commands=nvm + f"npx -y {cfg.SKILLS_CLI} add {cfg.PRETTY_MERMAID} -g -y"
             f" && test -f {quote(str(home / '.claude/skills/pretty-mermaid/SKILL.md'))}",
    _shell_executable="bash",
    _if=missing(f"test -f {quote(str(home / '.claude/skills/pretty-mermaid/SKILL.md'))}"),
)

# --- Python tools via uv -------------------------------------------------------------------
euporie_version = cfg.EUPORIE.split("==")[1]
with_args = " ".join(f"--with {quote(w)}" for w in cfg.EUPORIE_WITH)
server.shell(
    name=f"euporie {euporie_version} + ipykernel (uv tool, isolated)",
    commands=path + f"uv tool install --force {quote(cfg.EUPORIE)} {with_args}"
             ' && "$(uv tool dir)/euporie/bin/python" -c "import ipykernel"',
    _shell_executable="bash",
    _if=missing(path + f"uv tool list | grep -qx 'euporie v{euporie_version}'"
                ' && "$(uv tool dir)/euporie/bin/python" -c "import ipykernel"'),
)

# ax (Google's agentic orchestration CLI) is backlogged by the owner: docs/backlog.md.

# --- Bash completions from installed tools (kubectl + k, helm, gh, ax, rc) --------------
server.shell(
    name="bash completions: generate (temp file + bash -n; unmanaged files kept)",
    commands=f"bash {quote(str(src / 'completions.sh'))}",
    _shell_executable="bash",
)

# --- dev-disk-reclaim: report-only by default (--apply deletes) ---------------------------
files.put(name="dev-disk-reclaim (report-only by default)", src=str(src / "dev-disk-reclaim"),
          dest=str(bin_dir / "dev-disk-reclaim"), mode="755")
reclaim_units = {
    "dev-disk-reclaim.service": """[Unit]
Description=Report regenerable caches (dev-disk-reclaim, report only)

[Service]
Type=oneshot
ExecStart=%h/.local/bin/dev-disk-reclaim --dry-run
Nice=19
IOSchedulingClass=idle
""",
    "dev-disk-reclaim.timer": """[Unit]
Description=Report regenerable caches every night at 03:30

[Timer]
OnCalendar=*-*-* 03:30
Persistent=true

[Install]
WantedBy=timers.target
""",
}
changed = [
    files.put(name=f"dev-disk-reclaim unit: {unit}", src=StringIO("# Managed by t2-mac-kde (shell-user-tools)\n" + body),
              dest=str(units / unit), mode="644")
    for unit, body in reclaim_units.items()
]

# --- rclone mounts: config rclone_mounts = { remote = "Dir" } -> user services (never fstab) ---
mounts = dict(setting("rclone_mounts", cfg.RCLONE_MOUNTS))
cfg.validate_mounts(mounts)
# Prefer Nix's stable profile path (survives upgrades); fall back to whatever rclone is on PATH.
nix_rclone = home / ".nix-profile/bin/rclone"
rclone = str(nix_rclone) if nix_rclone.exists() else shutil.which("rclone")
if mounts and not rclone:
    print("shell-user-tools: rclone not installed; rclone mounts pending")
for remote, folder in (mounts.items() if rclone else ()):
    changed.append(files.put(name=f"rclone mount {remote}: -> ~/{folder} (user service)",
                             src=StringIO(cfg.rclone_unit(remote, folder, rclone, str(setting("rclone_cache_size", "10G")),
                                                           str(setting("rclone_cache_age", "24h")))),
                             dest=str(units / f"rclone-{remote}.service"), mode="644"))
# remotes removed from the config: stop, disable and delete their units
for unit in sorted(units.glob("rclone-*.service")) if units.exists() else ():
    if unit.stem.removeprefix("rclone-") not in mounts and "Managed by t2-mac-kde" in unit.read_text():
        systemd.service(name=f"{unit.name} removed from config: stop", service=unit.name, user_mode=True,
                        running=False, enabled=False)
        changed.append(files.file(name=f"remove {unit.name}", path=str(unit), present=False))

server.shell(name="systemd user daemon-reload", commands=["systemctl --user daemon-reload"],
             _if=lambda: any(op.did_change() for op in changed))
systemd.service(name="dev-disk-reclaim.timer (report-only)", service="dev-disk-reclaim.timer", user_mode=True,
                enabled=cfg.DEV_DISK_REPORT_TIMER, running=cfg.DEV_DISK_REPORT_TIMER)
for remote in (mounts if rclone else ()):
    systemd.service(name=f"rclone-{remote}.service enabled", service=f"rclone-{remote}.service",
                    user_mode=True, enabled=True, running=True)

# --- Bash loader last, so partially installed tools are not advertised ------------------
files.block(
    name="bash: load grml, history and turbo fragments (interactive shells only)",
    path=str(home / ".bashrc"),
    marker=cfg.BASH_MARKER,
    content=cfg.BASH_INIT,
    try_prevent_shell_expansion=True,
    backup=True,
)


# --- fish (optional, config shell_interactive = "fish"): every terminal hands over to fish --------
shell_interactive = setting("shell_interactive", "bash")
if shell_interactive not in ("bash", "fish"):
    raise ValueError('shell_interactive must be "bash" or "fish"')
fish = shell_interactive == "fish"
shell_prompt = setting("shell_prompt", "builtin")
if shell_prompt not in ("builtin", "starship"):
    raise ValueError('shell_prompt must be "builtin" or "starship"')
starship = shell_prompt == "starship"
fish_conf = home / ".config/fish/conf.d/t2-mac-kde.fish"
if fish:
    install_packages(PackageRequest(packages=("fish",), source="ubuntu"))
    files.put(name="fish: grml aliases, functions, prompt, safe-chain (~/.config/fish/conf.d/t2-mac-kde.fish)",
              src=StringIO(fish_shell.fish_conf(cfg.SAFE_CHAIN_WRAPPED if safe_chain else (), starship)),
              dest=str(fish_conf), mode="644", create_remote_dir=True)

    fish_data = home / ".local/share/fish"

    def _import_bash_history():
        """Once: fish starts with your bash history (suggestions work from day one)."""
        target, source = fish_data / "fish_history", home / ".bash_history"
        if target.exists() or not source.exists():
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        text = source.read_text(errors="replace")
        target.write_text(fish_shell.bash_history_to_fish(text, int(source.stat().st_mtime)))
        target.chmod(0o600)

    if not (fish_data / "fish_history").exists():
        python.call(name="fish: import ~/.bash_history once (fish_history did not exist yet)",
                    function=_import_bash_history)
    # Completions for every tool with a man page; once (re-run: fish_update_completions).
    server.shell(name="fish: completions generated from man pages (first time only)",
                 commands=[f"[ -d {quote(str(fish_data / 'generated_completions'))} ] || "
                           "fish -c fish_update_completions >/dev/null 2>&1 || true"])
elif fish_conf.exists() and "Managed by t2-mac-kde" in fish_conf.read_text():
    files.file(name="fish: our config removed (shell_interactive = bash)", path=str(fish_conf), present=False)
files.block(
    name=f"bash: hand over to fish at the first prompt ({'on' if fish else 'removed'})",
    path=str(home / ".bashrc"), marker=fish_shell.MARKER, content=fish_shell.BASHRC,
    present=fish, try_prevent_shell_expansion=True, backup=True,
)

# --- starship prompt (optional, config shell_prompt = "starship"): bash and fish ---------------
starship_toml = home / ".config/starship.toml"
if starship:
    install_packages(PackageRequest(packages=("starship",), source="ubuntu"))
    try:   # keep the palette hypr-termtheme last chose (default profile = cobalt)
        profile = (home / ".local/state/terminator-profile").read_text().strip()
    except OSError:
        profile = "default"
    themes_src = repo / "files/themes/foot/themes"
    files.put(name="starship: ~/.config/starship.toml (grml layout, language symbols, five palettes)",
              src=StringIO(starship_cfg.config({t: (themes_src / f"{t}.ini").read_text() for t in starship_cfg.THEMES},
                                               "cobalt" if profile == "default" else profile)),
              dest=str(starship_toml), mode="644", create_remote_dir=True)
elif starship_toml.exists() and starship_cfg.MARKER in starship_toml.read_text():
    files.file(name="starship: our config removed (shell_prompt = builtin)", path=str(starship_toml), present=False)
files.block(
    name=f"bash: starship prompt ({'on' if starship else 'removed'})",
    path=str(home / ".bashrc"), marker=starship_cfg.BASHRC_MARKER, content=starship_cfg.BASHRC,
    present=starship, before=True, line="BEGIN t2-mac-kde: ble.sh attach", try_prevent_shell_expansion=True,
    backup=True,
)

# --- ble.sh (optional): Kali/zsh-like suggestions, syntax colours, completion menu ----------
# Not with fish: fish has all of it built in, and ble.sh would only slow down bash's start.
blesh = bool(setting("shell_blesh", False)) and not fish
if blesh:
    install_packages(PackageRequest(packages=("ble.sh",)))
    files.put(name="ble.sh settings ~/.config/bash/blerc", src=str(src / "blerc"),
              dest=str(home / ".config/bash/blerc"), mode="644", create_remote_dir=True)
files.block(
    name=f"bash: ble.sh load at the top of ~/.bashrc ({'on' if blesh else 'removed'})",
    path=str(home / ".bashrc"), marker=cfg.BLESH_TOP_MARKER, content=cfg.BLESH_TOP,
    before=True, line=".*", present=blesh, try_prevent_shell_expansion=True, backup=True,
)
files.block(
    name=f"bash: ble.sh attach at the end of ~/.bashrc ({'on' if blesh else 'removed'})",
    path=str(home / ".bashrc"), marker=cfg.BLESH_END_MARKER, content=cfg.BLESH_END,
    present=blesh, try_prevent_shell_expansion=True, backup=True,
)


# --- aria2c: parallel downloads by default (every aria2c call; `dl` is a short alias) --------
files.put(name="aria2c defaults ~/.config/aria2/aria2.conf (16 connections, resume, retries)",
          src=str(src / "aria2.conf"), dest=str(home / ".config/aria2/aria2.conf"), mode="644",
          create_remote_dir=True)


# --- Compilers: config default_cc ("icx" = Intel oneAPI for your shells; unset = GCC) --------
# CC/CXX only in interactive user shells. Root, apt, DKMS and Kbuild stay on GCC (sudo resets the
# environment, the package helper runs apt with a fixed env, Kbuild sets its own CC).
default_cc = str(setting("default_cc", ""))
files.block(
    name=f"bash: compilers ({default_cc or 'gcc'}), GCC for Debian package builds, safe-chain aliases",
    path=str(home / ".bashrc"), marker=cfg.DEVTOOLS_MARKER, content=cfg.devtools_block(default_cc, safe_chain),
    before=True, line="BEGIN t2-mac-kde: ble.sh attach", try_prevent_shell_expansion=True, backup=True,
)
nim_cfg = home / ".config/nim/nim.cfg"
if default_cc == "icx":
    files.put(name="Nim: compile through icx/icpx (~/.config/nim/nim.cfg)", src=StringIO(cfg.NIM_CFG),
              dest=str(nim_cfg), mode="644", create_remote_dir=True)
elif nim_cfg.exists() and "Managed by t2-mac-kde" in nim_cfg.read_text():
    files.file(name="Nim: back to its default compiler (remove our nim.cfg)", path=str(nim_cfg), present=False)
# DKMS (not installed today; e.g. if a forked t2 kernel brings out-of-tree modules): never icx,
# even under `sudo -E`.
if os.path.exists("/usr/sbin/dkms") or os.path.exists("/usr/bin/dkms"):
    files.put(name="DKMS: always the kernel's GCC (unset CC/CXX)", src=StringIO(cfg.DKMS_GCC_ONLY),
              dest="/etc/dkms/framework.conf.d/10-t2-gcc-only.conf", mode="644", create_remote_dir=True,
              _sudo=True)


# --- nano: syntax highlighting (community set from Nix if present, else Ubuntu's) + settings --
nix_nano = home / ".nix-profile/share"
syntax = (str(nix_nano) + "/*.nanorc") if any(nix_nano.glob("*.nanorc")) else "/usr/share/nano/*.nanorc"
files.put(name=f"nano: ~/.config/nano/nanorc (syntax from {'Nix' if 'nix' in syntax else 'Ubuntu'})",
          src=StringIO(cfg.nanorc(syntax)), dest=str(home / ".config/nano/nanorc"), mode="644",
          create_remote_dir=True)
files.directory(name="nano backup dir", path=str(home / ".cache/nano/backups"), mode="700")


# --- Local history, directory navigation, file browser and Git diffs ----------------------
atuin_existing = home / ".config/atuin/config.toml"
if atuin_existing.exists():
    files.put(name="Atuin: preserve previous settings before local-only policy",
              src=StringIO(atuin_existing.read_text()),
              dest=str(atuin_existing.with_suffix(".toml.pre-t2")), mode="600",
              _if=lambda: not atuin_existing.with_suffix(".toml.pre-t2").exists())
files.put(name="Atuin: local-only history (no sync or update requests)",
          src=str(src / "atuin.toml"), dest=str(home / ".config/atuin/config.toml"),
          mode="600", create_remote_dir=True)
files.put(name="fish: Atuin, zoxide, Yazi and fzf previews",
          src=str(src / "navigation.fish"), dest=str(home / ".config/fish/t2-navigation.fish"),
          mode="644", create_remote_dir=True)
files.block(name="Git: delta pager", path=str(home / ".gitconfig"),
            marker="# {mark} t2-mac-kde: delta",
            content='[core]\n    pager = delta\n[interactive]\n    diffFilter = delta --color-only\n[delta]\n    navigate = true\n    syntax-theme = ansi',
            backup=True, try_prevent_shell_expansion=True)
