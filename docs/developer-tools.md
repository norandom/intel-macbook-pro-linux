# Developer tools

## Shell

`tasks/shell.py` keeps your `~/.bashrc` and only adds marked blocks to it. The Bash parts live in
`~/.config/bash/`:

- `grml.bash`: a grml-style prompt, `autocd`, spelling fixes for `cd`, `globstar`, the grml
  aliases (`l`, `la`, `ll`, `..`, ...), and a directory stack (`cd -2` jumps back two dirs).
- `history.bash`: 100,000 lines with timestamps, shared between all open terminals right away.
- `readline.inputrc`: type the start of a command, then Up/Down searches history by that prefix.
- Completions for kubectl (and the `k` alias), helm, gh and rc, generated from the installed
  tools.
- `dl` is `aria2c` with 16 connections, resume and retries (`~/.config/aria2/aria2.conf`).
- nano gets line numbers, mouse support, soft wrap and syntax highlighting.
- Neovim gets [nvim-simple](https://github.com/norandom/nvim-simple): CUA keys, a menu bar and
  pinned plugins (NERDTree, airline, quickui, devicons).

`shell_blesh = true` adds [ble.sh](https://github.com/akinomyoga/ble.sh): zsh-like inline
suggestions, syntax colours and a completion menu. Its settings are in
`~/.config/bash/blerc`. `false` and a re-run take it out of `~/.bashrc` again.

## Compilers

GCC and make come from Ubuntu. Intel's oneAPI `icx`/`icpx` are installed from Intel's apt repo
(`tasks/vendor_apps.py`) but stay off your PATH unless you ask:

```toml
default_cc = "icx"
```

Then interactive shells export `CC=icx CXX=icpx`, append the oneAPI bin directory to the end of
PATH (so it never shadows gcc or clang), and Nim compiles through icx. GCC is kept wherever it
matters for the system:

- root, sudo, apt and the package helper never see your CC/CXX;
- `dpkg-buildpackage` and `debuild` are wrapped to force GCC;
- the kernel build (Kbuild) picks its own compiler anyway;
- if DKMS is ever installed, a drop-in unsets CC/CXX for it, even under `sudo -E`.

One build with GCC: `CC=gcc make`. For Nim: `nim c --cc:gcc file.nim`.

## Node and Python

- Node comes from nvm, per user, at the version in `.nvmrc`. No system Node, no npm prefix
  override. Pinned npm globals: pnpm, GitHub Copilot CLI, OpenAI Codex CLI, ccusage.
- Python tools come through uv (`bootstrap.sh` installs it). euporie (Jupyter in the terminal)
  is installed as a uv tool.
- The pretty-mermaid skill is added for Claude Code.

## Safe Chain

```toml
safe_chain = true
```

Installs Aikido Safe Chain (`@aikidosec/safe-chain`, pinned) and aliases
`npm`, `npx`, `yarn`, `pnpm`, `pnpx`, `bun`, `bunx`, `pip`, `pip3`, `pipx`, `uv`, `uvx` and
`poetry` to its wrappers, which check packages for known malware before installing them. Its own
`safe-chain setup` isn't used, so your shell profiles aren't rewritten.

## Containers

`tasks/containers.py`:

- rootless Podman, with `docker` (podman-docker), `docker compose` and `docker-compose` running
  podman-compose. No daemon, no root socket.
- Short image names resolve to docker.io, like Docker.
- Linger is on, so containers keep running when you log out.
- A user `podman.socket` for podman-tui and Podman Desktop.
- An existing Docker install is detected and left alone; the shim is skipped then.

## Virtual machines

`tasks/virtualization.py` installs virt-manager on KVM with QEMU, OVMF (UEFI) and swtpm (a virtual
TPM, enough for Windows 11). Your user joins the `libvirt` group (next login), and libvirt's
default NAT network is started at boot. Guests use the host's route, including a Tailscale exit
node when one is on. Nested virtualization is already the kernel default; KVM is told to ignore
unknown MSRs so Windows guests with Hyper-V or WSL2 don't crash.

## Command-line tools from Nix

Most CLI tools come from one pinned Nix flake: zellij, kubectl, helm, k9s, ktop, Bitwarden CLI,
rclone, podman-tui, btop, ripgrep, fd, bat, jq, fzf, lazygit, glow, gh, gdu, trippy, multitail,
aria2, rustup, go, Nim, nimble, nimlangserver, netcat, gef, rizin and valgrind. Add your own with
`nix_tools_extra`. Updating, adding and rolling back: [nix.md](nix.md).

## iOS apps with xtool

[xtool](https://github.com/xtool-org/xtool) replaces Xcode for building and deploying iOS apps
with SwiftPM. The deploy unpacks the pinned AppImage into `~/.local/opt/xtool-<version>` (no
FUSE 2 needed) and links `xtool` into `~/.local/bin`. Once:

```sh
xtool setup     # Swift toolchain check, Apple Developer login, Darwin SDK from your Xcode.xip
```

You need an Apple ID and a downloaded `Xcode.xip`; xtool extracts the SDK from it. Then
`xtool new`, `xtool dev` build and run on a connected iPhone.

## Editors and GUI tools

VS Code, Zed, Sublime Text, Positron, Quarto, OpenIDEA, Typora, Neovim, NEdit and Meld; edb and
heaptrack for debugging; Chromium with a matching `chromedriver` for agents that drive a browser.
Where they come from: [apps.md](apps.md).

## Housekeeping

`dev-disk-reclaim` lists regenerable caches (Podman and Docker, build dirs in `~/.cache`) and
deletes them only with `--apply`. `t2-alerts` shows SSD health and service alerts, which new
shells also print until you `t2-alerts ack`.

## Change it

| You want | Change |
|---|---|
| Another prompt or aliases | `files/shell/grml.bash` |
| History size | `files/shell/history.bash` |
| Other npm globals | `NPM_TOOLS` in `manage/shell_tools.py` |
| Another Node version | `.nvmrc` |
| More CLI tools | `nix_tools_extra` in your config |
| icx, Safe Chain, ble.sh | `default_cc`, `safe_chain`, `shell_blesh` |

Re-run: `.venv/bin/pyinfra @local tasks/shell.py --use-sudo-password`.
