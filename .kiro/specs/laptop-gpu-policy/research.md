# Research and Design Readiness

## Summary

- Feature: laptop-gpu-policy.
- Discovery scope: integration with an existing physical-laptop configuration.
- Requirements approved by the user.
- Design finalization blocked by the uncaptured custom GPU systemd unit.

## Research Log

Rechecked visible /etc/systemd/system, /etc/modprobe.d and /etc/udev/rules.d.
Found apple-gmux.conf with force_igd=y and 30-amdgpu-pm.rules requesting AMD low
performance. No matching custom GPU systemd unit was found. Earlier runtime
observations showed the AMD driver bound and device active; this does not
invalidate the user's intended/current setup and must not trigger changes.

## Architecture Pattern Evaluation

Capture and reproduce the existing policy rather than design a new GPU switching
service. Selecting a replacement mechanism now would violate the approved
preservation requirement and risk external-display or suspend behavior.

## Design Decisions

The eventual GPU feature consumes the foundation's local execution and package
policy. It owns GPU-specific files and validation only. KDE and Hyprland consume
the same baseline. Foundation must not import or write GPU settings.

## Risks and Mitigations

The missing unit's name, contents, dependencies, helpers and enablement state
are necessary to determine startup ordering and actual power/display transitions.
Capture these before final design. Do not infer successful power-off from a
low-performance rule, or infer a broken policy from a loaded driver.

## Review Gate

NOT PASSED: existing configuration evidence is incomplete. Per the Kiro design
review gate, no finalized design.md is written for this feature. Required next
input is the custom unit's name/path or contents and referenced helper files.

## Subsequent protected-system instruction

The owner explicitly prohibits cryptsetup/LUKS/LVM, fstab/swap/resume,
kernel/modules/headers, bootloader and initramfs/mkinitcpio mutations or rebuilds.
See protected-system-boundary.md. This supersedes any earlier implication that
GPU reproduction might edit module/boot settings. Capture and preservation
checks remain read-only; no corrective change to the existing GPU setup is
authorized. Any eventual design must honor that stricter boundary.
