# Deferred source features

These items remain in the source inventory but are outside current installation
and configuration tasks, per explicit owner direction.

## Craft suite

- Reuse/evaluate the existing installer logic in source `tasks/apps.py` and
  `group_data/all.py: artcraft_apps` when this backlog item is reopened.
- Source entries: pdfcraft, designcraft, gridcraft, lightcraft, wordcraft,
  deckcraft and cadcraft; preserve their source versions/digests as provenance.
- Check Ubuntu-compatible permitted native artifacts then. No current download,
  installation, client-role activation or source host-role purge.

## LibreOffice

- Writer/Calc, German/English language dictionaries/support, source tabbed UI
  layer and Carlito office font are deferred together.
- Preserve the source package/profile inventory for later evaluation.
- Do not install/configure them as part of the current desktop port. Existing
  packages remain untouched; unrelated selected apps may retain shared existing
  dependencies without treating that as LibreOffice installation.

## ax (Google agentic orchestration CLI)

- Backlogged by the owner on 2026-11-15 after its `go install` (v0.3.1,
  GOTOOLCHAIN go1.27.2) failed in the first live deploy and stopped the run.
- When reopened: prefer an upstream release binary (pinned + sha256) over a Go
  build; keep it optional so a failure never blocks the rest of the deploy.

## Quiet pyinfra's files.block beta warning

- pyinfra 3.10 prints "The `files.block` operation is currently in beta!" for
  each managed ~/.bashrc block. Harmless; silence it with a logging filter in
  manage/preflight.py when convenient (owner request 2026-11-15, low priority).
