# Deferred source features

These items remain in the source inventory but are outside current installation
and configuration tasks, per explicit owner direction.

## ax (Google agentic orchestration CLI)

- Backlogged by the owner on 2026-11-15 after its `go install` (v0.3.1,
  GOTOOLCHAIN go1.27.2) failed in the first live deploy and stopped the run.
- When reopened: prefer an upstream release binary (pinned + sha256) over a Go
  build; keep it optional so a failure never blocks the rest of the deploy.

## Quiet pyinfra's files.block beta warning

- pyinfra 3.10 prints "The `files.block` operation is currently in beta!" for
  each managed ~/.bashrc block. Harmless; silence it with a logging filter in
  manage/preflight.py when convenient (owner request 2026-11-15, low priority).

## Hibernate

- Done 2026-11-16: works on the owner's MacBookPro16,1 (swap 80 GiB, HibernateMode=shutdown,
  T2 driver reload around hibernate, lid closes into hibernate). Details: `docs/known-issues.md`.

## Verbose boot and shutdown

- Backlogged by the owner on 2026-11-16. Runbook ready: `docs/verbose-boot.md` (owner-run
  removal of `quiet splash` from GRUB; protected bootloader config). Until then: press Esc
  during boot or shutdown to see the messages.

## Fan curves

- 2026-11-16: the t2 kernel's macsmc_hwmon driver rejects writes to fan*_target (EOPNOTSUPP),
  and t2fanrd targets the old applesmc files, so custom fan curves aren't possible now.
  Revisit with a newer t2 kernel / the owner's t2 fork (test: docs/t2-tests/test2.sh).

## CPU mitigations off

- Done 2026-11-16: config `cpu_mitigations_off` (tasks/cpu_mitigations.py). Before:
  `benchmarks/linux.json`, after: `benchmarks/mitigations-off/linux.json` (syscalls +27 %).
  Kept off; results in `docs/benchmark.md`.

## Contour terminal

- Requested by the owner on 2026-11-16 for later. Not in Ubuntu 26.04; upstream publishes
  Ubuntu .debs on GitHub (contour-terminal/contour). When reopened: a pinned, sha256-checked
  .deb through the vendor-apps path, plus a palette for each of the five themes so
  hypr-termtheme switches it like foot and Ghostty. It's in the app inventory as `backlog`.

## ICC display profiling on Wayland

- Backlogged by the owner on 2026-11-17; documentation only, no deployment changes.
- Idea: use a panel-specific ICC profile for the built-in Apple Color LCD. Start
  with the profile from this same Mac's macOS installation, or measure this panel
  with a colorimeter and DisplayCAL/ArgyllCMS for a profile reflecting its current condition.
- Current Hyprland 0.53.3 uses the sRGB preset and has no native ICC-file monitor
  option. Revisit native ICC support with a planned update of the pinned Hyprland
  stack; do not upgrade it just for this backlog item. Plasma Wayland offers an
  alternative through its display configuration.
- Importing a profile into colord alone does not apply desktop-wide correction:
  the active compositor must use it. Keep the profile specific to the physical
  panel, not the virtual RDP output. Disable rabbit filters and night shift when
  measuring or checking color accuracy.
- References: [Hyprland 0.53 monitor settings](https://wiki.hypr.land/0.53.0/Configuring/Monitors/),
  [newer Hyprland ICC support](https://wiki.hypr.land/0.55.0/Configuring/Basics/Monitors/),
  [Plasma Wayland profiling guide](https://zamundaaa.github.io/wayland/2024/07/16/how-to-profile.html).
