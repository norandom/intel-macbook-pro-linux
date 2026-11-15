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
SKILLS_CLI = 'skills@1.8.1'
PRETTY_MERMAID = 'imxv/pretty-mermaid-skills@pretty-mermaid'

# Python tools via uv (isolated tool environments).
EUPORIE = 'euporie==2.10.4'
EUPORIE_WITH = ('ipykernel==7.4.0',)

AX_VERSION = 'v0.3.1'
AX_GO_TOOLCHAIN = 'go1.27.2'

# Owner-configured rclone remotes -> mount dir relative to $HOME, e.g. {'onedrive': 'OneDrive'}.
# Empty by default: no mount units are written until the owner adds a configured remote.
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


def rclone_unit(remote: str, folder: str, rclone: str) -> str:
    return f"""# Managed by t2-mac-kde (shell-user-tools)
[Unit]
Description=rclone mount {remote}: on ~/{folder}
After=network-online.target
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Type=notify
# Skipped until the remote exists (rclone config)
ExecCondition=/bin/sh -c '{rclone} listremotes | grep -qx {remote}:'
ExecStartPre=/bin/mkdir -p %h/{folder}
ExecStart={rclone} mount {remote}: %h/{folder} --vfs-cache-mode full --vfs-cache-max-size 2G --dir-cache-time 5m
ExecStop=/bin/fusermount3 -uz %h/{folder}
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
"""
