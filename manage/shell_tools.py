"""Pins and managed snippets for tasks/shell.py (shell-user-tools)."""

BASH_MARKER = '# {mark} t2-mac-kde: shell-user-tools'
# Sourced after the foundation block (nvm, ~/.local/bin). Interactive shells only.
# turbo.bash is owned by laptop-resource-policy; only sourced when readable.
BASH_INIT = '''if [[ $- == *i* ]]; then
    for __t2_f in "$HOME/.config/bash/grml.bash" "$HOME/.config/bash/history.bash" \\
                  "$HOME/.config/t2-mac-kde/turbo.bash"; do
        [ -r "$__t2_f" ] && . "$__t2_f"
    done
    unset __t2_f
fi'''

# ble.sh (optional, config shell_blesh): load early, attach last, as its README recommends.
BLESH = "/usr/share/blesh/ble.sh"
BLESH_TOP_MARKER = "# {mark} t2-mac-kde: ble.sh load, must stay first"
BLESH_TOP = '[[ $- == *i* && -r ' + BLESH + ' ]] && source ' + BLESH + ' --noattach --rcfile "$HOME/.config/bash/blerc"'
BLESH_END_MARKER = "# {mark} t2-mac-kde: ble.sh attach, must stay last"
BLESH_END = '[[ ${BLE_VERSION-} ]] && ble-attach'

INPUTRC_MARKER = '# {mark} t2-mac-kde: shell-user-tools'
INPUTRC_INIT = '''$include /etc/inputrc
$include ~/.config/bash/readline.inputrc'''

NVIM_SIMPLE_COMMIT = '70717b469ce15ade8b1186c3650a484a5202cb75'
NVIM_PLUGINS = {
    'skywind3000/vim-quickui': '48aaa496633eb39eb8759921386e29e9867fb623',
    'vim-airline/vim-airline': '8dc1bd0a116de527f6bc58c1d04386ba357c624f',
    'vim-airline/vim-airline-themes': '77aab8c6cf7179ddb8a05741da7e358a86b2c3ab',
    'preservim/nerdtree': '690d061b591525890f1471c6675bcb5bdc8cdff9',
    'ryanoasis/vim-devicons': '71f239af28b7214eebb60d4ea5bd040291fb7e33',
}

# npm globals under the foundation nvm Node (no prefix override), exact versions.
NPM_TOOLS = {
    'pnpm': '12.21.0',
    '@github/copilot': '1.0.112',
    '@openai/codex': '0.169.0',
    'ccusage': '20.0.51',
}
# Aikido Safe Chain (AGPL-3.0): malware check before npm/pip/uv/... installs (config safe_chain).
# Pinned to a release at least two weeks old; its own `safe-chain setup` (rewrites profiles) is not used.
SAFE_CHAIN = ('@aikidosec/safe-chain', '1.5.27')
SAFE_CHAIN_WRAPPED = ('npm', 'npx', 'yarn', 'pnpm', 'pnpx', 'bun', 'bunx', 'pip', 'pip3', 'pipx', 'uv', 'uvx', 'poetry')

ICX_BIN = '/opt/intel/oneapi/compiler/latest/bin'
DEVTOOLS_MARKER = '# {mark} t2-mac-kde: compilers, package-build safety, safe-chain'


NIM_ICX = ("--cc:clang --clang.exe=icx --clang.linkerexe=icx "
           "--clang.cpp.exe=icpx --clang.cpp.linkerexe=icpx")


def devtools_block(safe_chain: bool = False) -> str:
    """Interactive shells only. GCC is the compiler everywhere (C, C++, cgo, Rust's cc-rs, Nim, V);
    Intel oneAPI only on request: `intel <command>` runs one command with CC=icx CXX=icpx, and
    `nim-icx` compiles Nim through icx. Root, apt, DKMS and Kbuild never see a CC from here."""
    lines = ['if [[ $- == *i* ]]; then',
             '  # Intel oneAPI on request: intel make | intel cmake -B build | intel go build | nim-icx c x.nim',
             f'  if [ -x {ICX_BIN}/icx ]; then',
             f'    intel() {{ CC=icx CXX=icpx PATH="$PATH:{ICX_BIN}" "$@"; }}',
             f'    nim-icx() {{ PATH="$PATH:{ICX_BIN}" nim {NIM_ICX} "$@"; }}',
             '  fi',
             '  # Debian package builds honour an exported CC: always GCC there (kernel/Kbuild ignores CC anyway)',
             '  dpkg-buildpackage() { CC=gcc CXX=g++ command dpkg-buildpackage "$@"; }',
             '  debuild() { CC=gcc CXX=g++ command debuild "$@"; }']
    if safe_chain:
        for tool in SAFE_CHAIN_WRAPPED:
            lines.append(f'  command -v aikido-{tool} >/dev/null && alias {tool}=aikido-{tool}')
    lines.append('fi')
    return '\n'.join(lines)


DKMS_GCC_ONLY = """# Managed by t2-mac-kde: DKMS builds kernel modules with the kernel's GCC, even under sudo -E.
unset CC CXX
"""

NANO_SETTINGS = """set linenumbers
set constantshow
set mouse
set softwrap
set atblanks
set tabsize 4
set tabstospaces
set autoindent
set indicator
set minibar
set zap
set backup
set backupdir "~/.cache/nano/backups"
"""


def nanorc(syntax_glob: str) -> str:
    """One syntax set only (duplicate definitions make nano complain)."""
    return ("# Managed by t2-mac-kde (shell-user-tools): syntax highlighting + editor settings.\n"
            f'include "{syntax_glob}"\n' + NANO_SETTINGS)


SKILLS_CLI = 'skills@1.8.1'
PRETTY_MERMAID = 'imxv/pretty-mermaid-skills@pretty-mermaid'

# Python tools via uv (isolated tool environments).
EUPORIE = 'euporie==2.10.4'
EUPORIE_WITH = ('ipykernel==7.4.0',)

AX_VERSION = 'v0.3.1'
AX_GO_TOOLCHAIN = 'go1.27.2'

# Repository default for config rclone_mounts (remote -> dir under $HOME), e.g. {'onedrive': 'OneDrive'}.
# Empty: no mount units are written until the owner configures remotes.
RCLONE_MOUNTS: dict[str, str] = {}

# Report-only nightly dev-disk-reclaim timer; off by default.
DEV_DISK_REPORT_TIMER = False


def validate_mounts(mounts: dict[str, str]) -> None:
    import re
    seen = set()
    for remote, folder in mounts.items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+', remote):
            raise ValueError(f'rclone remote name {remote!r} must be [A-Za-z0-9_-]+')
        if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', folder) or folder in seen:
            raise ValueError(f'rclone mount dir {folder!r} must be one plain, unique directory name under $HOME')
        seen.add(folder)


def rclone_unit(remote: str, folder: str, rclone: str, cache_size: str = "10G", cache_age: str = "24h") -> str:
    """User service, never fstab: starts after login, never blocks boot or shutdown, and keeps
    retrying (30 s growing to 10 min) while offline (airport, train) instead of giving up."""
    return f"""# Managed by t2-mac-kde (shell-user-tools)
[Unit]
Description=rclone mount {remote}: on ~/{folder}
After=network-online.target
# retry forever while offline
StartLimitIntervalSec=0

[Service]
Type=notify
# Skipped until the remote exists (rclone config)
ExecCondition=/bin/sh -c '{rclone} listremotes | grep -qx {remote}:'
ExecStartPre=/bin/mkdir -p %h/{folder}
# Full VFS cache: opened files stay local, writes land in the cache and upload in the background
# (write-back), so edits survive a dropped connection. Parallel transfers, read-ahead and chunked
# reads for throughput; generous retries and short connect timeouts for flaky links.
ExecStart={rclone} mount {remote}: %h/{folder} \\
  --vfs-cache-mode full --vfs-cache-max-size {cache_size} --vfs-cache-max-age {cache_age} \\
  --vfs-write-back 10s --vfs-read-ahead 128M --vfs-read-chunk-size 32M \\
  --vfs-read-chunk-size-limit 512M --buffer-size 32M \\
  --transfers 8 --checkers 16 --multi-thread-streams 4 \\
  --dir-cache-time 1h --poll-interval 1m \\
  --contimeout 15s --timeout 1m --retries 10 --retries-sleep 10s --low-level-retries 10
# lazy unmount: logout/shutdown never waits on an unreachable remote
ExecStop=/bin/fusermount3 -uz %h/{folder}
TimeoutStopSec=10
Restart=on-failure
RestartSec=30s
RestartSteps=5
RestartMaxDelaySec=10min

[Install]
WantedBy=default.target
"""
