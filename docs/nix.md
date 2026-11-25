# Nix for the command-line tools

The command-line tools I use every day come from Nix: one flake in `nix/`, one lock file
(`nix/flake.lock`) that pins all of them, and one entry in my Nix profile called `t2-tools`.
Nix itself is Ubuntu's package (`nix-setup-systemd`), so there is no curl-pipe installer and the
daemon runs from the package's own systemd units. `/nix` sits on the normal root filesystem.

## What Nix covers, and what it doesn't

Nix: zellij, kubectl, helm, k9s, ktop, bw (bitwarden-cli), rclone, lazydocker, ctop, btop, ripgrep,
fd, bat, jq, fzf, lazygit, glow, gh, gdu, trippy, multitail, aria2, nc (netcat-openbsd), gef, rizin,
valgrind, go, and Nim (nim, nimble, nimlangserver). The full list is `nix_tools` in `files/config.example.toml`.

Not Nix:

- GUI apps (Zed, Satty, the Craft apps, OpenIDEA, browsers, editors). On Ubuntu they need
  OpenGL glue (nixGL), and the .deb or tarball routes work fine.
- Hyprland, KDE, the kernel, drivers, audio and anything that runs as a system service: apt.
- uv: the bootstrap needs it before Nix exists, so it stays in `~/.local/bin`.
- Node and npm: nvm.
- GUI debuggers: apt. pwndbg was removed from nixpkgs, so it isn't here either.
- upmd and rc (rustfs-cli): not in nixpkgs, so they stay pinned GitHub releases. Careful, the
  `rc` in nixpkgs is the Plan 9 shell, a different program.

The apt copies of btop, ripgrep, golang-go and friends stay installed (root and other users use
them). In my shell and in Hyprland, Nix wins because `~/.nix-profile/bin` comes first in PATH.

## Update everything

```sh
t2-nix-update
```

It runs `nix flake update` in `~/.local/share/t2-mac-kde/nix/` (the deploy's copy of the flake
plus a `tools.json` made from my config), upgrades the `t2-tools` profile entry, copies the new
`flake.lock` back to the repo and prints which versions changed. Then commit the lock:

```sh
git -C ~/Source/t2-mac-kde add nix/flake.lock && git -C ~/Source/t2-mac-kde commit -m "nix: update tools"
```

On another machine, a deploy with that commit installs exactly the same versions.

## Add or remove a tool

Edit `nix_tools` in `~/.config/t2-mac-kde/config.toml` (nixpkgs attribute names, e.g.
`kubernetes-helm` for helm; look them up on search.nixos.org), then deploy:

```sh
.venv/bin/pyinfra @local tasks/nix_tools.py
```

Take zellij, kubectl, kubernetes-helm, k9s, ktop, bitwarden-cli or rclone out of the
list and the next `tasks/apps.py` run brings back the
pinned release binary. `nix_tools = []` leaves an empty profile entry; to drop it entirely:
`nix profile remove t2-tools`.

## Pin and roll back

- `nix profile rollback` goes back to the previous tool set; `nix profile history` lists them.
- To go back to an older lock for good: `git revert` (or `git checkout <rev> -- nix/flake.lock`)
  and deploy again.

## Disk space

A weekly user timer (`nix-gc.timer`) deletes profile generations older than 30 days and
collects garbage. By hand: `nix-collect-garbage --delete-older-than 30d`, or `nix store gc` for
just the unreferenced paths. `du -sh /nix/store` shows the total.

## Which binary wins?

```sh
type -a btop
```

The first line should be `~/.nix-profile/bin/btop`. If it isn't, open a new shell (the PATH
block lives in `~/.bashrc`); for apps started from Hyprland, log in again.

## Rust and Nim

rustup comes from the Ubuntu archive, not Nix. Nix's rustup patches every toolchain it
downloads to run on Nix's glibc, so build scripts and proc-macros (linked against the system
glibc) ran inside a Nix-glibc compiler, and Nix's garbage collection could break the toolchain.
Ubuntu's rustup keeps rust-lang.org toolchains as they are; the deploy reinstalls toolchains the
Nix rustup had patched, with the same components. Linker, `cc` and `pkg-config` are the
system's, so GUI binaries link against the system's GTK, WebKit, X11 and Wayland libraries.

rustup comes without a toolchain. Fetch one once:

```sh
rustup default stable
```

Nim (compiler, nimble and nimlangserver) comes from Nix; it compiles its C through the
system's GCC, so the programs it builds link only against system libraries. Through Intel's
icx instead: `nim-icx c app.nim` (see [developer-tools.md](developer-tools.md#compilers)).

## First install notes

- The deploy adds you to the group `nix-users` (the daemon socket is only open to it). New
  logins have the group; until then `t2-nix-update` switches to it by itself, and plain `nix`
  commands need `sg nix-users -c 'nix profile list'` or a fresh login.
- The first install creates `flake.lock` in `~/.local/share/t2-mac-kde/nix/`. Copy it into the
  repo once and commit it: `cp ~/.local/share/t2-mac-kde/nix/flake.lock nix/`.

## Adding a tool without copying the whole list

Put it in `nix_tools_extra` in `~/.config/t2-mac-kde/config.toml`, e.g.
`nix_tools_extra = ["nchat", "hyperfine"]`, and run the deploy (or `t2-nix-update`).
`nix_tools` replaces the default list entirely; use it only if you want to drop defaults.
