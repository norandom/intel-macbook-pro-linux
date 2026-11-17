# Requirements: workstation usability (retrospective backfill)

## Status and purpose

**Backfilled on 2026-11-17 for documentation, after implementation.** This spec records
existing behavior; it does not claim that requirements/design approval preceded the code.
**There is deliberately no tasks.md:** the owner requested a retrospective record, not a
new implementation plan. Existing feature checklists retain their own history. Approval
flags remain unset; implementation and live validation are different states.

The laptop owner needs a comfortable, consistent desktop and shell on the Intel 16-inch
T2 MacBook. Recent changes add night-time display controls, sharp legacy apps, fish and
Starship, file icons, CLI tools, familiar multiplexer keys and a simpler deployment entrypoint.

## Recorded scope

- Commit `a32a42b8f9561655d0151f9030c353e3f4d234fe`: night shift, X11 scaling,
  app-menu fixes, fish/Starship and palette integration.
- Related commit `25947a102ab5de1bfc52e65c3f8389f3175106c4`: Clapper's GStreamer
  packages without gstreamer1.0-libav, archive lftp/byobu, and deferred Contour.
- Current working-tree additions: Nix lftp/byobu/eza/uutils, fish aliases, multiplexer
  bindings, open-file limits, deploy.sh and the targeted pyinfra warning filter.
  These additions are not represented as committed or live-deployed.

## Requirements

### R1. Desktop usability
- When night_shift is enabled, the configuration shall run gammastep for the Hyprland
  session using configured coordinates or the local timezone city's coordinates.
- The Waybar control shall expose night-shift status and allow pausing/resuming it.
- At fractional scale, the desktop shall disable XWayland compositor scaling and configure
  Xft DPI and selected legacy application fonts for sharp rendering.
- When a desktop ID cannot be used through uwsm, the app menu shall support its Exec entry;
  recent items shall be read as whole lines.

### R2. Interactive shell and appearance
- When shell_interactive is fish, interactive Bash shall hand over at its first prompt,
  preserving its environment while leaving scripts and explicit Bash sessions available.
- Fish shall provide the existing aliases/functions, history import, completions, fzf
  integration, duration display and completion notifications.
- When shell_prompt is starship, Bash and fish shall use the shared Starship configuration.
- Palette switching shall update fish syntax colours and Starship's palette selection.
- When eza is installed, interactive fish ls shall show file icons on terminal output;
  icon rendering requires a suitable font. Starship remains responsible for prompt symbols.

### R3. CLI tools
- The default Nix tool set shall include lftp, byobu, eza and uutils-coreutils.
- Interactive fish shall alias available prefixed Rust utilities, preserving fish builtins;
  eza shall take precedence for ls. System utilities and scripts shall remain unchanged.
- The earlier archive packages shall not be removed by this change.

### R4. Multiplexers
- Zellij and Byobu's tmux backend shall use Ctrl+A as their prefix.
- Prefix c/n/p/d shall create, select next/previous, or detach; [ shall enter scrollback;
  s/v shall split down/right; Tab shall change pane; a shall send Ctrl+A to the application.
- Other Emacs control keys shall reach the application in normal mode. Byobu copy mode
  shall use Emacs keys; Zellij shall provide arrow, Ctrl+P/N and page navigation in scroll mode.
- Managed edits shall preserve existing configuration through backups.

### R5. Limits and deployment
- Resource policy shall configure soft/hard NOFILE limits of 65536/1048576 for PAM
  logins and systemd system/user managers. Existing processes keep inherited limits;
  reboot is the documented activation route and service overrides may still apply.
- deploy.sh shall invoke the repository venv's pyinfra with @local deploy.py, forward
  arguments, work from another current directory, reject root and report a missing venv.
- Normal deployment shall request sudo authentication; --dry shall avoid proactively
  requesting it, although privileged facts may still require authentication.
- Repository pyinfra configuration shall suppress only the exact files.block beta warning,
  preserving all other diagnostic messages and exit status.

## Constraints and exclusions

The protected boot/storage boundary and guarded archive installs continue to apply.
Agents do not live-deploy or authenticate sudo. VM network/mount/GRUB/module tuning is not
adopted by this backfill; the existing inotify floor remains. A natively pinned editable fish prompt is not implemented; the later terminal trials
provide a Terminator latest-command label and Warp native command blocks. Contour remains backlog. This document does not authorize work
on those exclusions or replace the parent feature specs.

## Subsequent owner-requested additions (2026-11-17)

This section also records implemented working-tree changes retrospectively; there is
still no tasks.md because this document is a backfill.

- R6: Atuin history shall remain local through disabled auto-sync, update checking and
  daemon use, plus a loopback sync endpoint enforced in fish. Deployment shall not log in
  or import/sync history. Delta, Yazi, fzf previews and zoxide shall integrate with fish.
- R7: Both terminal approaches shall be available for comparison: a Terminator latest-command
  header and Warp's native sticky command headers/top input. Terminator shall remain default.
  Warp shall use a pinned verified user-level vendor payload, guarded distro dependencies,
  disabled telemetry/crash reporting/account sync, and the five existing palettes.
  Its other network features are not represented as disabled or sandboxed.
- R8: Ubuntu technical reports/software usage consent, whoopsie uploads by default,
  MOTD news fetching, popularity-contest participation and ubuntu-report autostart shall
  be disabled without disabling local crash diagnostics or security updates.
- R9: SSH shall listen on all IPv4/IPv6 interfaces. RDP TCP/UDP 3389 shall remain limited
  to Tailscale and loopback; direct LAN transport is preferred by Tailscale but not guaranteed.

## Owner correction: Terminator-only pinned entry

This correction supersedes R7 and the earlier Warp trial description. Warp is removed
from provisioning and palette switching; cleanup on the next owner deploy removes only
the exact managed trial artifacts. Personal data/backups remain.

Terminator shall offer a top single-line edit field matching the terminal font and
colours, with a separator below. Fish prompt readiness shall enable that field and
disable output-pane input. Submission shall restore native terminal input until the
next fish prompt. A Native toggle shall retain access to fish completion, Atuin and
multiline editing. GTK-field history is per-pane and session-only. This is an input
prototype, not a full shell renderer or command-aware scrollback implementation.

## Owner correction: prototype disabled

The owner subsequently disabled the Terminator pinned-input prototype to move it to a
separate project. This supersedes its active-integration requirements/design above.
Theme deployment removes CommandHeader from enabled_plugins; shell deployment removes
the hooks and restores normal directory titles. The inactive Python plugin and fish
companion remain in the repository for extraction, without deployment. Existing sessions
need the plugin disabled in Preferences or a restart after deployment.
