# Design: Nix for user CLI tools

## Overview
`tasks/nix_tools.py` (new module, after `apps` in `deploy.py`) installs Ubuntu's Nix packages,
enables flakes for the user, and keeps one Nix profile entry `t2-tools` built from `nix/flake.nix`.

```
config nix_tools ─┐
                   ├─> nix/flake.nix (buildEnv "t2-tools") ─ nix/flake.lock (nixpkgs pin, committed)
repo default ─────┘                         │
                                            ▼
                       nix profile install/upgrade  ->  ~/.nix-profile/bin  (first in PATH)
```

## Components
- **Packages**: `nix-setup-systemd` (+ `nix-bin`) via the guard; `nix-daemon.socket` enabled.
  Ubuntu's package creates the `nixbld` users/group and `/nix`; no other system file is written
  except an owned `/etc/nix/nix.custom.conf`-style drop-in only if user config is insufficient.
- **User config**: `~/.config/nix/nix.conf`: `experimental-features = nix-command flakes`.
- **Flake** (`nix/flake.nix`): input `nixpkgs` (pinned by `flake.lock`, branch nixos-unstable or the
  current stable release, decided in implementation); output `packages.x86_64-linux.default =
  buildEnv { name = "t2-tools"; paths = map (n: pkgs.${n}) tools; }`. The tool list is passed in as
  a generated `nix/tools.json` (from config) read with `builtins.fromJSON`, so config changes don't
  edit Nix code.
- **Profile**: `nix profile install ./nix#default` first time; afterwards `nix profile upgrade` on
  the entry when `tools.json` or `flake.lock` changed (stamp file in `~/.local/state/t2-mac-kde/`).
- **PATH**: an owned `~/.bashrc` block (marker without regex metacharacters) placing
  `$HOME/.nix-profile/bin` before `~/.local/bin` and `/usr/bin`; uwsm `env-hyprland` gets the
  same, so launchers in Hyprland see Nix tools.
- **GC**: user units `nix-gc.service` / `.timer` (weekly): `nix-collect-garbage --delete-older-than 30d`.

## Default tool set (owner policy: prefer Nix where possible)
All user CLI tools nixpkgs provides: the GitHub-release set (zellij, kubectl, kubernetes-helm, k9s,
bitwarden-cli, rclone, podman-tui) and the user-facing apt CLI tools (btop, ripgrep, fd, bat, jq, fzf,
lazygit, glow, gh, gdu, trippy, multitail, aria2, atop stays apt: it is a system service).
The apt copies stay installed (harmless, other users/root) but Nix wins in PATH. `ktop`,
`rc` and `upmd` stay on their release route until a nixpkgs attribute is confirmed. Satty, Zed and
other GPU/GTK apps stay where they are (Nix GL apps on non-NixOS need nixGL; out of scope).

## Decisions
- Ubuntu's Nix package instead of the upstream installer: guarded, no curl|sh, apt-owned daemon units.
- Flake + lock in repo instead of channels: reproducible, one-command update, reviewable diff.
- Config-driven list instead of code: matches `manage/userconfig.py` conventions.

## Risks
- Disk use under `/nix` (GC timer; documented `nix store gc`).
- PATH precedence surprises: `which` check in tests and README.
- nixpkgs attribute renames on update: the flake build fails before anything changes (no partial state).
