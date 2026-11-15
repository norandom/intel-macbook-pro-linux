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
from pyinfra.operations import files, server, systemd

from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
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

# --- rclone mounts (owner-configured remotes only; RCLONE_MOUNTS is empty by default) -----
rclone = shutil.which("rclone")
if cfg.RCLONE_MOUNTS and not rclone:
    print("shell-user-tools: rclone not installed; rclone mounts pending")
for remote, folder in (cfg.RCLONE_MOUNTS.items() if rclone else ()):
    changed.append(files.put(name=f"rclone mount {remote}: -> ~/{folder} (user service)",
                             src=StringIO(cfg.rclone_unit(remote, folder, rclone)),
                             dest=str(units / f"rclone-{remote}.service"), mode="644"))

server.shell(name="systemd user daemon-reload", commands=["systemctl --user daemon-reload"],
             _if=lambda: any(op.did_change() for op in changed))
systemd.service(name="dev-disk-reclaim.timer (report-only)", service="dev-disk-reclaim.timer", user_mode=True,
                enabled=cfg.DEV_DISK_REPORT_TIMER, running=cfg.DEV_DISK_REPORT_TIMER)
for remote in (cfg.RCLONE_MOUNTS if rclone else ()):
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


# --- ble.sh (optional): Kali/zsh-like suggestions, syntax colours, completion menu ----------
blesh = bool(setting("shell_blesh", False))
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
