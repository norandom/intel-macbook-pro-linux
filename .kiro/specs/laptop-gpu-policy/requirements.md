# Requirements Document

## Project Description (Input)
The owner of this T2 Linux Mac laptop wants local system management to
preserve their existing graphics behavior: use the Intel integrated GPU during
normal laptop operation while no external display is attached, and retain AMD
GPU availability for external displays where required by the existing setup.
This policy applies to the current KDE desktop and the planned full Hyprland
session alongside it. The existing login screen, authentication settings, and
default session must be preserved.

The user reports that they already disabled the AMD GPU for normal operation
using modprobe.d configuration and a custom systemd unit. The desired change is
to capture and reproduce that working setup through this repository's
uv-managed pyinfra workflow, rather than replace it with a newly invented GPU
switching mechanism. Node/npm remain managed by nvm as established in the
local-system-foundation spec.

Prior read-only inspection found Intel UHD Graphics 630 and AMD Navi 14
hardware, `/etc/modprobe.d/apple-gmux.conf` containing
`options apple-gmux force_igd=y`, and a udev rule requesting AMD's low
performance level. In that inspection's environment, the AMD driver was still
loaded and bound, and runtime power status read `active`. These observations
do not establish the behavior of the user's subsequent changes. The custom
systemd unit's name, contents, dependencies, and activation state have not yet
been captured, and no automatic external-display switching behavior has been
verified.

Capture the actual modprobe configuration, custom unit, relevant helper files,
and activation relationships before specifying implementation. Preserve Intel
rendering for internal-display use and existing external-display support.
Evaluate cold boot, display attach/detach, and suspend/resume behavior against
the working baseline. Do not equate a loaded AMD driver with the user's GPU
policy being incorrect, or claim that low performance mode proves power-off.
Do not re-enable AMD unconditionally, force VM software rendering, or import
GPU patches intended for the source VM. Exact device power transitions and
external-display handling remain evidence to collect from the existing setup.

This spec owns capture and preservation of laptop GPU policy. The foundation
spec owns uv/pyinfra/nvm; future desktop and RDP specs consume this GPU policy.
Further context is recorded in
`../local-system-foundation/port-intake.md`.

## Introduction

Preserve and reproduce the owner's working Intel-first graphics policy on the
T2 Mac laptop, including existing external-display behavior, for KDE and the
planned full Hyprland session.

## Boundary Context

- **In scope:** capture of the existing GPU configuration and unit, Intel use
  without an external display, preservation of external-display support, and
  verification across boot and suspend/resume.
- **Out of scope:** a new GPU switching mechanism, desktop installation, RDP,
  login changes, and unrelated power tuning.
- **Adjacent expectations:** local-system-foundation provides deployment and
  package policy. Desktop integration consumes this policy without overriding it.
- **Evidence prerequisite:** the user's custom systemd unit remains uncaptured.
  Its behavior must be established before a reproduction design can be finalized.

## Requirements

### Requirement 1: Capture the working configuration
**Objective:** As the laptop owner, I want my existing graphics setup recorded,
so that it can be reproduced accurately.

#### Acceptance Criteria
1. When capturing the host baseline, the management workflow shall record the GPU-related configuration files, custom unit, helper files, and activation relationships that implement the owner's existing policy.
2. If a required unit or helper cannot be identified or read, the management workflow shall report the missing evidence and leave GPU changes unapplied.
3. When reporting the baseline, the management workflow shall distinguish the owner's intended policy, observed file contents, and verified runtime behavior.

### Requirement 2: Preserve Intel-first laptop operation
**Objective:** As the laptop owner, I want Intel graphics for internal-display use,
so that my existing laptop configuration remains intact.

#### Acceptance Criteria
1. While no external display is attached, the managed laptop configuration shall preserve Intel iGPU use for the desktop.
2. The managed laptop configuration shall preserve the existing AMD-disable behavior used for normal laptop operation.
3. The management workflow shall avoid unconditionally enabling AMD or forcing software rendering when integrating Hyprland.
4. When evaluating GPU state, the management workflow shall report rendering-device selection separately from driver loading and device power state.

### Requirement 3: Preserve external-display and session behavior
**Objective:** As the laptop owner, I want existing display behavior retained,
so that desktop changes do not break laptop use.

#### Acceptance Criteria
1. When an external display is attached, the managed laptop configuration shall preserve the existing setup's external-display support, including AMD availability where that setup requires it.
2. When an external display is detached, the managed laptop configuration shall preserve the existing setup's return to internal-display operation.
3. When the laptop boots or resumes, the managed laptop configuration shall preserve the established display and GPU behavior for the attached-display state.
4. The GPU deployment shall preserve the existing login screen, authentication settings, and default session.
5. Where a full Hyprland session is installed, the desktop integration shall honor the same GPU policy as KDE.
6. If required display-state behavior has not been verified, the management workflow shall report validation as pending rather than claim the GPU policy is reproduced.
