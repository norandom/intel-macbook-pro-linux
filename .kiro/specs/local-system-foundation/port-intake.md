# Laptop port intake

Status: user input and preliminary evaluation; requirements, design, task
generation and system deployment have not been approved by this document.
This intake extends the initial scope and supersedes its Hyprland exclusion.

## Requested behavior

Use uv and pyinfra for local management, with nvm-managed Node/npm.
Port selected capabilities from
[hyperland-forky-worker-vm](https://github.com/norandom/hyperland-forky-worker-vm).
Retain KDE and the existing login arrangement. No autologin.

### CPU turbo and shell

Persist turbo disabled at boot using `/etc/tmpfiles.d/no-turbo.conf`:

```text
w /sys/devices/system/cpu/intel_pstate/no_turbo - - - - 1
```

Apply using `sudo systemd-tmpfiles --create /etc/tmpfiles.d/no-turbo.conf`
and verify the sysfs value is `1`. Check that the interface exists before
attempting to manage it. Preserve the requested interactive Bash aliases:

```bash
alias turbo-on='echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo'
alias turbo-off='echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo'
alias turbo-status='cat /sys/devices/system/cpu/intel_pstate/no_turbo'
```

These aliases change runtime state; the tmpfiles rule restores the disabled
default at boot. Preserve existing shell customization and nvm initialization.
The source's Bash configuration, completion, history, and helpers are requested.

### Memory, tuning, and services

- Evaluate zram, earlyoom, reclaim sysctls, journald and coredump limits.
- Evaluate the source tuning individually for a physical laptop.
- Bluetooth is required. snitchd is excluded. Avahi should be disabled.
- Printing may be needed: retain CUPS capability rather than importing the
  source's blanket CUPS disable list. Printer connection details remain open.
- Preserve laptop power management and hardware support.

### Containers, fonts, and user tools

- Containers are required; source implementation uses rootless Podman,
  Docker-compatible commands, Compose, and user services.
- Fonts are required; source includes JetBrainsMono/FiraCode Nerd Fonts and
  Fixedsys fonts with fontconfig and X11 support.
- User tools are required, including the requested btop and Neovim port.
  Inventory the source tools before specifying individual packages, mounts,
  accounts, credentials, cleanup timers, and host-specific extras. Keep the
  established nvm installation rather than importing the source npm prefix.

### Hyprland, widgets, themes, and remote access

- Add a full GPU-backed Hyprland session alongside KDE, selectable through
  the existing login/session chooser. Preserve the existing login screen,
  authentication settings, and default session. To change desktops, log out
  and select the desired session. A nested Hyprland window is not requested.
- Prefer reuse of source widgets and desktop helpers: Waybar and its graphs,
  launcher/app menu, quota display, theme switching, clipboard tools, keyboard
  and layout helpers, and applicable window controls.
- Themes are required. Source CLI/application themes are candidates for direct
  reuse; compositor effects, KDE integration, and terminal coupling need review.
- hypr-rdp is required; scope it to the intended Hyprland session.
- Exclude source GPU/software-rendering patches intended for the VM. Inspect
  each patch separately, including RDP codec/protocol changes; do not assume
  all hypr-rdp patches are GPU workarounds.
- No autologin and no removal of KDE, Plasma, or SDDM.

## Observed host baseline

Read-only inspection on 2026-11-15 found Ubuntu 26.04.1, T2 kernel
`7.3.4-3-t2-resolute`, Bash, KDE Wayland, Intel UHD 630 and AMD Navi 14
graphics. RAM is approximately 64 GB (62 GiB reported); existing disk swap
is 16 GB (15 GiB reported), unused at inspection. `no_turbo` reads `1`.
No new system configuration was applied during this intake.
Service state could not be established by the initial systemctl probe;
do not infer enabled/disabled state from its empty output.

## Preliminary port evaluation

Source files inspected: `tasks/memory.py`, `tuning.py`, `services.py`,
`containers.py`, `fonts.py`, `desktop.py`, `shell.py`, `themes.py`,
`hypr_rdp.py`, selected `files/system/*`, and relevant `group_data/all.py` values.

| Area | Assessment and next validation |
| --- | --- |
| zram | Candidate for porting. Source uses lz4, half RAM, priority 100. Size and reclaim policy must account for this host's substantial RAM and existing disk swap. Preserve disk swap and check resume/hibernation configuration. Avoid live swap recreation under pressure. |
| earlyoom | Candidate, with explicit KDE/Plasma/KWin session protection in addition to Hyprland. Source only lists its VM desktop stack and prefers killing browsers; evaluate that policy and coexistence with other OOM managers. |
| journal/core limits | Source journal limits are 500M persistent/100M runtime; coredump storage limits are 500M with 1G kept free. Candidate defaults pending review of the host's actual crash handler; these coredump settings only affect systemd-coredump. |
| reclaim tuning | Evaluate individually; do not copy the entire swappiness/cache/watermark/dirty-writeback set as a performance claim. |
| VM kernel arguments | Exclude haltpoll arguments and the source's `mitigations=off` / `audit=0` defaults. Preserve current T2 boot arguments. |
| filesystem tuning | Do not import `commit=60` or the live root remount wholesale. Determine filesystem and durability implications first; assess noatime independently. |
| network tuning | BBR/fq and source buffer/TCP settings require kernel and workload checks; keep optional pending evidence. |
| limits | inotify/open-file increases may help development workloads; compare actual limits first. Preserve watchdog and hardware modules unless evidence supports a change. |
| VM services | Exclude QEMU agent and serial-console setup. Preserve Bluetooth and power-management services. |
| printing without Avahi | Direct printer IP/hostname configuration is possible; automatic DNS-SD discovery may be unavailable. Keep printing requirements open until the printer is identified. |
| containers | Check Ubuntu package availability, subordinate UID/GID ranges, existing Docker/Podman installs, and behavior of linger/socket activation before adopting source defaults. |
| widgets and themes | Prefer original assets/scripts where compatible. Review compositor plugin dependencies, executable paths, quota/auth dependencies, fonts, terminals, and session service activation. KDE should not start Hyprland-only helpers. |
| GPU desktop / RDP | Verify native GPU output and hybrid GPU selection, suspend/resume, portals, input, and supported Hyprland/plugin/RDP versions. Do not reuse forced llvmpipe/headless settings or blank the laptop display automatically. |

References: [intel_pstate interface](https://docs.kernel.org/admin-guide/pm/intel_pstate.html),
[CUPS network printing](https://openprinting.github.io/cups/doc/network.html).

## Open points for subsequent content

- Printer connection, suspend/hibernation expectations, preferred memory limits,
  RDP network/authentication requirements, and exact user-tool selection.

Possible future boundaries: foundation; laptop power/memory/services;
containers; shell/tools/fonts; Hyprland/widgets/themes; Hyprland RDP.
These are candidates, not an approved roadmap or completed discovery.

## Existing GPU configuration to preserve and capture

The user reports disabling the AMD GPU through modprobe.d and adding a systemd
unit. Capture that unit and its dependencies as part of the laptop baseline;
its name/content are still needed. Hyprland should target the intended Intel
GPU configuration rather than automatically enabling the AMD GPU.

Read-only inspection found `/etc/modprobe.d/apple-gmux.conf`:

```conf
# Enable the iGPU by default if present
options apple-gmux force_igd=y
```

Also found `/etc/udev/rules.d/30-amdgpu-pm.rules`:

```udev
KERNEL=="card[012]", SUBSYSTEM=="drm", DRIVERS=="amdgpu", ATTR{device/power_dpm_force_performance_level}="low"
```

These are the observed file contents, not proof that the AMD device is powered
off. In the environment visible to the inspection, `amdgpu` remained loaded,
PCI device `0000:03:00.0` was bound to it, and its runtime power status read
`active`. No explicit AMD blacklist or matching custom GPU systemd unit was
found in the inspected configuration directories. This may differ from the
user's newly changed host state; reconcile against the supplied unit and files
before drawing conclusions or making changes. Preserve the existing T2 kernel
arguments and verify display/suspend behavior before managing GPU power.

The dedicated `../laptop-gpu-policy/requirements.md` now captures the clarified
Intel-first laptop policy and preservation of existing external-display support.
It is initialized; implementation details await capture of the existing unit.

## Source inventory and missing port work

See [the source-derived port plan](../../../docs/source-port-plan.md) for the
complete task-module disposition and 23 proposed port work items. This corrects
the earlier foundation-only implementation plan; feature design is still needed.
