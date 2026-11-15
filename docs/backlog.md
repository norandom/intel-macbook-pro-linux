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
