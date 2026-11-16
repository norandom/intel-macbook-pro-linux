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

## Hibernate (suspend to disk)

- Backlogged by the owner on 2026-11-15. Kernel, resume device (swap LV, 252:1) and
  systemd units are ready, but 16 GiB disk swap vs 64 GiB RAM makes it fail under load.
- When reopened: owner-run swap LV resize keeping path + UUID (docs/hibernate-swap.md),
  then a guarded Hibernate power-menu entry (see git history: hypr-hibernate).

## Verbose boot and shutdown

- Backlogged by the owner on 2026-11-16. Runbook ready: `docs/verbose-boot.md` (owner-run
  removal of `quiet splash` from GRUB; protected bootloader config). Until then: press Esc
  during boot or shutdown to see the messages.
