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

- 2026-11-16: swap LV grown to 80 GiB (owner, live USB); config `hibernate` built (polkit rule +
  guarded menu entry). First test: the kernel hangs right after "PM: hibernation: hibernation
  entry" / "Filesystems sync" (forced power-off needed). Cause: the T2 bridge drivers (t2bce_*,
  formerly apple-bce) don't survive the hibernation freeze. The t2linux workaround unloads them
  before sleep and reloads them after, which the protected boundary forbids (and which can lose
  keyboard and trackpad). `hibernate = false` again; revisit with a newer t2 kernel.

## Verbose boot and shutdown

- Backlogged by the owner on 2026-11-16. Runbook ready: `docs/verbose-boot.md` (owner-run
  removal of `quiet splash` from GRUB; protected bootloader config). Until then: press Esc
  during boot or shutdown to see the messages.

## Fan curves

- 2026-11-16: the t2 kernel's macsmc_hwmon driver rejects writes to fan*_target (EOPNOTSUPP),
  and t2fanrd targets the old applesmc files, so custom fan curves aren't possible now.
  Revisit with a newer t2 kernel / the owner's t2 fork (test: ~/t2-tests/test2.sh).

## CPU mitigations off

- Done 2026-11-16: config `cpu_mitigations_off` (tasks/cpu_mitigations.py). Before:
  `benchmarks/linux.json`, after: `benchmarks/mitigations-off/linux.json` (syscalls +27 %).
  Kept off; results in `docs/benchmark.md`.
