# Tasks: Nix for user CLI tools

- [ ] 1. `tasks/nix_tools.py`: guarded install of `nix-setup-systemd`, enable `nix-daemon.socket`,
      user `~/.config/nix/nix.conf` (flakes) (req 1)
- [ ] 2. `nix/flake.nix` + `nix/tools.json` rendering from config `nix_tools`; commit `nix/flake.lock` (req 2.1, 2.2)
- [ ] 3. Profile install/upgrade with a change stamp; `nix profile rollback` documented (req 2.3, 2.4)
- [ ] 4. PATH block in `~/.bashrc` and uwsm `env-hyprland` (req 3.1)
- [ ] 5. Move every user CLI tool nixpkgs has to the Nix set: release-route tools leave RELEASE_TOOLS,
      apt user tools stay installed but resolve to Nix; dispositions + report; list exceptions (req 0, 3.2)
- [ ] 6. Weekly GC user timer (req 4.1); `nix_tools = []` path verified (req 4.2)
- [ ] 7. Tests (req 5.1), dry run (5.2), README "Handy commands" (`nix flake update`, rollback),
      config example, owner live check (5.3)
