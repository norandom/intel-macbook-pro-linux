# Requirements: Nix for user CLI tools

## Introduction
Today every CLI tool that Ubuntu doesn't package well (zellij, kubectl, helm, k9s, ktop, bw, rc,
rclone, upmd, podman-tui, ...) is a GitHub release with its own pinned version and SHA256 in
`manage/applications.py`. Updating means bumping each pin by hand. The owner wants Nix for these
user tools because one lock file (`flake.lock`) pins them all, `nix flake update` refreshes them
together, and nixpkgs builds them reproducibly. Tools that want newer versions than Ubuntu ships
(btop and similar) can come from Nix too.

Scope is user-level command-line tools only. Hyprland, the kernel, drivers, system services,
desktop integration and GPU/OpenGL applications stay with apt or their current route.

## Requirements

### 1. Install Nix the Ubuntu way
- 1.1 Nix is installed from Ubuntu's archive (`nix-setup-systemd`, which brings `nix-bin`) through
  `manage.packages.install_packages` (package guard: no removals, archive scan). No curl|sh installer.
- 1.2 The multi-user daemon (`nix-daemon`) runs from the package's systemd units; the desktop user
  needs no root for profile operations.
- 1.3 Flakes and the `nix` command are enabled for the user (`experimental-features`), without
  editing package-owned files outside a single owned drop-in or the user's `~/.config/nix/nix.conf`.
- 1.4 `/nix` lives on the existing root LV. No fstab, LVM, kernel, bootloader or initramfs change
  (protected-system-boundary).

### 0. Owner policy: prefer Nix where possible
- 0.1 User-level CLI tools come from Nix whenever nixpkgs has them, including tools currently
  installed via apt only for the user (e.g. btop, ripgrep, fd, bat, jq, fzf, lazygit, glow, gh)
  and every GitHub-release pin.
- 0.2 apt remains the route for system, desktop, hardware and service packages (Hyprland, KDE,
  PipeWire, drivers, daemons, GUI apps with system integration).
- 0.3 GitHub-release pins remain only for tools nixpkgs does not provide; each such exception is
  listed with the reason.

### 2. One pinned tool set
- 2.1 The repository holds a flake (`nix/`) whose default package is a `buildEnv` of the selected
  tools; `nix/flake.lock` pins nixpkgs and is committed.
- 2.2 The tool list comes from the user config (`nix_tools`, attribute names in nixpkgs) with a
  repository default; personal additions never require code edits.
- 2.3 Deploy installs or upgrades that environment into the user's Nix profile idempotently.
- 2.4 Updating all tools = `nix flake update` in `nix/` (committed lock) + one deploy. Rollback =
  `nix profile rollback` (documented).

### 3. Coexistence and precedence
- 3.1 A tool provided by Nix wins over the same command from apt or a GitHub-release binary in
  `~/.local/bin`: the Nix profile's `bin` comes first in PATH for interactive shells and the
  Hyprland session.
- 3.2 Migrated GitHub-release tools are removed from the release route in the same change, so each
  tool has exactly one owner (no duplicate installs, application report stays accurate).
- 3.3 nvm (Node), uv (Python tools) and apt (system packages) keep their roles.

### 4. Hygiene and reversibility
- 4.1 Old generations are garbage-collected on a schedule (user timer, e.g. weekly, keep 30 days).
- 4.2 `nix_tools = []` (or removing the module from the deploy) leaves the system working: the
  release route or apt still covers what was migrated back, and the profile can be removed with
  documented commands.
- 4.3 No Snap/Flatpak, and no Nix-managed desktop apps or services.

### 5. Verification
- 5.1 Unit tests: flake package list renders from config; PATH block order; migrated tools absent
  from RELEASE_TOOLS.
- 5.2 Dry run lists the apt install, daemon enablement and profile operation.
- 5.3 Live check (owner): `which btop zellij kubectl` resolve to `~/.nix-profile/bin`; versions match
  the lock.
