# Desktop Consumer Contracts

These seams preserve existing source behavior and separate feature ownership.
They do not assert a running desktop. The chosen native0.53 backport consumes
these independent theme/font/application producer contracts. No newer compositor
build or private library closure is required.

## Terminal and theme producer: coordinated-themes

- `/usr/local/bin/hypr-term [terminal arguments...]`: themes-owned executable,
  resolves its selected terminal/profile, forwards arguments without flattening
  them and returns the launched command's result. Desktop uses it through its
  session launcher and never supplies terminal configuration files.
- `~/.local/bin/hypr-termtheme <profile>|next|prev|apply`: themes-owned executable.
  Preserve source command names and profile mapping. `next`/`prev` cycle the
  source order default→navy→fixedsys→cream→petrol; `apply` re-applies current selection without
  cycling. Empty input means next. apply omits source live Terminator/bar/notification
  actions. Invalid/extra profile arguments exit2 and leave selection unchanged.
  Invalid state/runtime failures exit1; missing terminal executable exits127. Other
  failures are nonzero with a diagnostic. No compositor is required to switch
  terminal/editor themes.
- Source compatibility state is `~/.local/state/terminator-profile`, a one-line
  selected source profile name; missing state means `default` (maps to cobalt).
  Known values are default,navy,fixedsys,cream,petrol. Invalid/multiline state
  is an error, not default. Themes owns writing and atomic publication last. Desktop reads validated known
  names only and never writes that file. The compatibility path ignores XDG_STATE_HOME overrides. Theme spec may add richer status but
  must preserve this compatibility read contract or explicitly revise consumers.
- Waybar's theme module refresh signal is RTMIN+10. Themes may notify an existing
  same-user desktop bar after a successful change. Missing bar/compositor is a
  normal standalone case and cannot make a successful theme change fail.
  Desktop must restrict refresh/reload actions to its selected session rather
  than indiscriminately kill all same-name user processes.
- Hyprland notifications are optional best-effort consumer feedback. No desktop
  startup, install or private-library environment is required for theme commands.
- Desktop Fuzzel terminal launching consumes the same terminal executable;
  source `terminal=terminator -x` must be adapted by the eventual desktop design
  to the themes-owned launch contract with equivalent desktop-entry handling.

## Font producer: desktop-fonts

Invoke `/usr/local/bin/hypr-xfonts` after initial Xwayland readiness and when its
instance changes. Its zero exit may be an optional-directory skip; use the
font provisioning report and real core-font queries for acceptance. Exit1 is
readiness/registration failure with bounded wait; exit2 is usage failure.
Do not duplicate or rewrite its implementation at ~/.local/bin.

## Application producer: application-suite

Read `$XDG_STATE_HOME/t2-mac-kde/applications.json` (default ~/.local/state),
schema_version1, entries by stable application ID. Missing/stale report is
unknown. Re-probe the selected executable before launch. Desktop does not install
an app on click, silently substitute browsers or claim blocked vendor routes
installed. Preserve unavailable entries with useful feedback.

## Session consumer: hyprland-rdp

`hypr-session status --json [--instance SIGNATURE]` exposes schema_version1,
uid, instance_signature, compositor_executable, compositor_version, plugin_abi,
wayland_display, nullable x_display, runtime_dir, bus_address and state
preparing/ready/stopping. It is read-only, defaults only to current explicit
HYPRLAND_INSTANCE_SIGNATURE and requires matching user/socket/liveness.
Missing/ambiguous/wrong-user selection exits2 with unavailable/reason; never
choose an instance by newest-directory timestamp or persist full environments.

RDP consumes that native0.53 session/protocol identity and owns all remote
monitor/input/cursor/audio/service transitions. Desktop does not start RDP units.
Ephemeral status is private under the selected runtime; stale state is not proof
of a live ready session. Missing GPU-unit evidence blocks reproduction/transition
validation only. SDDM, dormant KDE and protected boot/storage state are preserved.

## GTK seam

Themes owns scoped Terminator tab CSS and its preserving import into user
gtk.css. Desktop owns initial GTK settings.ini only and does not overwrite
gtk.css or theme-owned imports. Native desktop Fuzzel uses terminal=hypr-term -x.

## Native RDP compatibility boundary

The RDP feature's selected upstream maintainer release archive has its own
minimum-compositor/API gate (current documentation may require0.54+). Desktop
stays on the explicit native0.53 backport baseline. RDP may report incompatibility;
it must not upgrade/build the compositor or reintroduce fork patches through
this desktop contract.
