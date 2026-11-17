# Design: workstation usability (retrospective backfill)

**Documentation written after implementation on 2026-11-17. No tasks.md is generated
because this is a backfill, not a prospective implementation workflow.** The requirements
capture the implemented intent; this design identifies the current code and limitations.

## Components and requirement mapping

| Requirements | Implementation | Design |
| --- | --- | --- |
| R1 | manage/night_shift.py; tasks/desktop.py; files/desktop/bin/hypr-nightshift; hypr-gammastep.service | Local coordinate lookup, validated temperatures, session service and Waybar toggle; no network geolocation. |
| R1 | files/desktop/bin/hypr-xscale; files/desktop/hypr/looknfeel.conf; autostart.conf | Zero XWayland scaling plus application DPI/font adjustments at login. |
| R1 | files/desktop/bin/hypr-appmenu | Exec fallback for desktop IDs; line-preserving recent list. |
| R2 | manage/fish_shell.py; manage/starship.py; tasks/shell.py | Bash first-prompt handover, generated fish conf.d content and optional Starship initialization. |
| R2 | tasks/themes.py; files/themes/bin/hypr-termtheme | Five terminal palettes supply fish colours and the active Starship palette. |
| R3 | manage/nix_tools.py; files/config.example.toml; tasks/nix_tools.py | Extend the default profile package list; existing Nix config selection/override behavior remains. |
| R2, R3 | manage/fish_shell.py | Discover executable ~/.nix-profile/bin/uutils-* commands; skip builtins; install interactive aliases, then prefer eza for ls if available. |
| R4 | tasks/multiplexers.py; files/shell/zellij-screen.kdl; byobu-screen.tmux | User config operations included in deploy.py; backed-up marked blocks. |
| R5 | tasks/resource_policy.py | Owned systemd system/user manager drop-ins and PAM limits.d file; no forced restart of user workloads. |
| R5 | deploy.sh; config.py | Shell entrypoint uses exec to preserve pyinfra status; logging.Filter rejects one exact warning message. |

## Integration decisions

Zellij reads the first keybinds node. The managed block is inserted before an existing
keybinds node, preserving other preferences and the old node for rollback. Its clear-defaults
setting removes conflicting default shortcuts. Byobu is configured for tmux; its final
.tmux.conf applies Screen-style shortcuts and Emacs copy-mode settings. Configuration paths
respect XDG_CONFIG_HOME and BYOBU_CONFIG_DIR, with the existing ~/.byobu directory preferred
when no explicit override exists. New sessions are the documented activation route.

Rust coreutils use nixpkgs' prefixed commands rather than replacing /usr/bin programs.
Fish aliases do not propagate into system scripts; command cp bypasses the alias. eza icons
are separate from Starship and need a Nerd Font. No new Starship repair was necessary:
a fresh fish session already loaded it successfully.

NOFILE drop-ins use /etc/systemd/{system,user}.conf.d/60-t2-nofile.conf and
/etc/security/limits.d/60-t2-nofile.conf. They set defaults, not a guarantee for every process:
existing processes and per-service overrides can retain different limits.

The warning filter lives in repository config.py, so normal repository pyinfra invocations
as well as deploy.sh load it. It does not lower the log level, filter stderr wholesale,
modify the installed dependency, or hide other warnings. A different --config file can
bypass this repository preference.

## Related specifications

This record supplements ../hyprland-desktop/, ../coordinated-themes/, ../shell-user-tools/,
../nix-user-tools/, ../application-suite/ and ../laptop-resource-policy/. It does not rewrite
those specs or retrospectively assert approval. The core steering filenames product.md,
tech.md and structure.md were absent at backfill time; existing custom steering applies.

## Verification and deployment status

Earlier checks in this session passed 299 unit tests, fish syntax/source checks, Zellij
configuration parsing and an isolated tmux prefix check. Shell, Nix and multiplexer dry runs
passed at that point. Subsequent resource-policy and full-deploy dry runs stopped during
privileged fact collection at a sudo password prompt; they are not successful deployment
validation. deploy.sh passed bash syntax validation. The logging filter is validated
separately when added; these historical checks do not establish live behavior after reboot.

Owner live deployment, fresh terminal/multiplexer sessions, icon rendering, desktop visual
behavior and post-reboot resource-limit checks remain pending. These are recorded status
limitations, not invented implementation tasks. The repository currently lacks a committed
nix/flake.lock; this pre-existing reproducibility gap is not resolved by this backfill.

## Subsequent integration details

R6 uses files/shell/atuin.toml and navigation.fish, deployed by tasks/shell.py, plus
Nix defaults in manage/nix_tools.py. Atuin initializes after fzf and owns Ctrl+R;
Up remains native fish. The loopback endpoint is configuration defense, not a firewall.
Yazi's cwd-file wrapper changes the shell directory on exit; ff uses fd and bat.
Delta uses the terminal ANSI palette. A backed-up marked Git configuration block selects it.

R7 uses files/themes/terminator/plugins/command_header.py with a fish_preexec/title
hook. A GTK label sits outside each VTE scroll area and accepts the T2CMD title prefix;
it displays the most recent command, not the command associated with old scrollback.
The plugin follows profile colours. tasks/warp.py unpacks the SHA256-pinned official
.deb under ~/.local/opt without running scripts that add an apt source/key. Native
library dependencies use the normal guard. tasks/themes.py supplies Warp settings
and five YAML palettes; hypr-termtheme changes the active YAML and managed font settings.
Warp's GUI behavior and refresh semantics still need owner validation.

R8 extends tasks/resource_policy.py; the installed machine already has whoopsie masked,
while ubuntu-report/popularity-contest were absent at inspection. GNOME consent settings
and MOTD news controls cover the installed reporting paths; Ubuntu Pro/security services
are not removed or disabled. R9 adds explicit wildcard ListenAddress entries to the
existing sshd drop-in; ss showed both wildcard listeners already active. The RDP nftables
asset is unchanged. Other host/network firewall rules can still affect LAN reachability.

302 unit tests passed after these additions, including hostile inherited Atuin environment
values, privacy settings and the RDP rule boundary. Shell, Nix and Warp dry runs passed;
themes, remote-access and resource-policy previews may stop at privileged facts without
sudo authentication. No live deployment or GUI validation has been performed by the agent.

## Superseding design: pinned input and Warp removal

The owner subsequently chose to remove Warp. tasks/warp.py, its theme assets and
switcher target were removed; tasks/remove_warp.py is the narrow cleanup migration.
The installed payload remains until the owner deploys that migration.

CommandHeader now uses Gtk.Entry above a Gtk.Separator. Fish emits T2READY at prompt
and T2CMD at execution; the plugin gates editing and VTE input based on these states.
Enter changes state before sending bytes to prevent duplicate submissions, clears a
native draft with Emacs Ctrl+A/Ctrl+K, and sends the command to the existing PTY.
Running commands keep native PTY input. Native mode restores fish editing explicitly;
unloading the plugin restores VTE input. The field adopts VTE's actual font and the
profile colours on refresh. GTK entry offers basic editing/history only; shell
completion/Atuin/multiline entry require Native mode. Fish prompts/echo remain below.
Mock-widget behavior checks cover readiness, input gating, submission, duplicate
prevention and unrelated title changes; actual GUI verification remains pending.

## Owner correction: prototype disabled

The owner subsequently disabled the Terminator pinned-input prototype to move it to a
separate project. This supersedes its active-integration requirements/design above.
Theme deployment removes CommandHeader from enabled_plugins; shell deployment removes
the hooks and restores normal directory titles. The inactive Python plugin and fish
companion remain in the repository for extraction, without deployment. Existing sessions
need the plugin disabled in Preferences or a restart after deployment.
