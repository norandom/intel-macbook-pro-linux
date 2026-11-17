# Tasks: Nix for user CLI tools

- [x] 1. `tasks/nix_tools.py`: guarded install of `nix-setup-systemd`, enable `nix-daemon.socket`, user joins `nix-users` (socket is root:nix-users 0770), `~/.config/nix/nix.conf` (flakes) (req 1)
- [x] 2. `nix/flake.nix` (nixos-26.05) + `tools.json` from config `nix_tools`, rendered to `~/.local/share/t2-mac-kde/nix/` (repo tree stays clean) (req 2.1, 2.2)
- [ ] 2b. Deferred (owner): commit `nix/flake.lock` after the first profile install (`cp ~/.local/share/t2-mac-kde/nix/flake.lock nix/`)
- [x] 3. Profile install/upgrade via `t2-nix-update --apply` with stamp `~/.local/state/t2-mac-kde/nix-tools.sha`; `t2-nix-update` for updates; rollback in docs/nix.md (req 2.3, 2.4)
- [x] 4. PATH block in `~/.bashrc` (before ble.sh attach, after ~/.local/bin) and uwsm `env-hyprland`; completions.sh sees Nix (req 3.1)
- [x] 5. Release tools zellij/kubectl/helm/k9s/ktop/bw/rclone + podman-tui -> disposition `nix` (pins kept as RELEASE_FALLBACK); our marked binaries removed once Nix provides them; apt tools listed `nix_preferred` (req 0, 3.2)
- [x] 5b. Exceptions: upmd, dagger, pwndbg (removed) not in nixpkgs; rc stays release (nixpkgs rc = Plan 9 shell); uv (bootstrap), node (nvm); Craft apps/OpenIDEA not in nixpkgs (GUI .debs)
- [ ] 5c. Deferred: dagger has no nixpkgs attribute (needs a release pin or dagger's own flake)
- [x] 6. Weekly `nix-gc.timer` (user, via sg nix-users) (req 4.1); `nix_tools = []` -> release fallback (tested) (req 4.2)
- [x] 7. Tests `tests/test_nix_tools.py`, dry run, README handy commands + docs/nix.md, config example
- [ ] 7b. Owner live check (5.3): deploy, then `type -a btop zellij kubectl` resolve to `~/.nix-profile/bin`
- [x] Default CLI set extended with lftp, byobu, eza and prefixed uutils-coreutils; live profile update remains owner-run.
