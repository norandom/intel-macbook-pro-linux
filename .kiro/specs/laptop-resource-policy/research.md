# Research & Design Decisions

## Summary
- **Feature:** laptop-resource-policy; P01–P06.
- **Discovery scope:** full discovery for a new host-policy integration, using actual pinned source, local read-only inspection and upstream manuals.
- **Key findings:** source zram restart swaps devices immediately; source tuning and service list are VM-specific. The local handler actually invokes systemd-coredump, so its storage limits are applicable after refresh. systemd bus access is unavailable in this tool environment; service state and runtime acceptance are unverified.
- **Skills:** kiro-spec-init, requirements (EARS/review gate), design (full/light discovery, synthesis, principles/review gate), tasks (generation/parallel/sanity gates), verify-completion and spec-status. Templates were read. Core steering product.md, tech.md and structure.md do not exist; roadmap.md/package-policy.md and actual foundation code supply available context.

## Research Log

### Provenance and owner input
Inspected `/tmp/t2-source-audit/tasks/memory.py`, `tuning.py`, `services.py`, `shell.py`, `group_data/all.py`, local `deploy.py`, `tasks/tools.py`, `pyproject.toml`, AGENTS.md, feature brief, roadmap, package policy, source-port-plan and foundation `port-intake.md`. Source revision is `a1c09ec3f02a98b7c6a4641f907108a2ad080993`.

Fetched the following missing assets through GitHub plugin at that exact revision; contents and tree blob identities were inspected:

| Asset | Git blob |
|---|---|
| files/system/99-memory.conf | 78bde239245044bb7f4f170d201ee7db45532e6e |
| files/system/90-net.conf | a2312a14d65e222b4ce66c6b85c97df148831220 |
| files/system/earlyoom | 96bbe05375eba6988f73fbc44ef3a104bb8237a8 |
| files/system/journald.conf | e177bec098f9cee1118d76956ed258232e864e5e |
| files/system/coredump.conf | d95af0dfe7072a01fb50a688b4df32ced7bd0819 |

Source earlyoom `--avoid` reduces victim score, despite its comment saying “never kill”; it does not guarantee exclusion. User's exact aliases and tmpfiles rule are in foundation intake, not source shell.py. The shell feature consumes a separate resource-owned fragment.

### Fresh host inspection, 2026-11-15
Read-only commands obtained `/etc/os-release`, `/proc/meminfo`, `/proc/swaps`, `/proc/cmdline`, `/proc/sys/kernel/core_pattern`, selected sysctls, package metadata, CPU turbo interface and mount views. No settings were applied.

| Observation | Result and limits |
|---|---|
| OS/kernel | Ubuntu 26.04.1; command line retains T2 7.3.4-3, intel_iommu=on, iommu=pt, pm_async=off |
| RAM | MemTotal 65,730,820 KiB, approximately 62.7 GiB physical usable RAM |
| Disk swap | /dev/dm-1, 16,777,212 KiB, zero used, priority -1; fstab names /dev/mapper/vg0-swap |
| Resume | No readable explicit resume entry in probed default grub/resume file; another initramfs config is permission-denied. This is not evidence hibernation is configured or works. |
| Turbo | no_turbo reads 1 |
| Crash handler | core_pattern pipes to /usr/lib/systemd/systemd-coredump; installed systemd and systemd-coredump 259.9-0ubuntu0.1 |
| Available packages | apt-cache: systemd-zram-generator 1.2.1-2 and earlyoom 1.9.0-1; neither installed in query output. This checks metadata, not dependency simulation/install success. |
| Existing reclaim | swappiness 60; cache pressure 100; page-cluster 3; boost 15000; scale 10; dirty byte caps 0; writeback 500 |
| Existing limits | watches 559994; instances 128; current process nofile 4096:524288; watchdog 1 |
| Network | cubic; default_qdisc unavailable from this restricted view |
| Mount view | ext4 relatime plus sandbox read-only flags; tmpfs /tmp approximately half RAM. Sandbox mount flags are not authoritative host fstab policy. |
| systemctl | is-system-running/show fail with Operation not permitted on system bus. No enabled/running service state established. |

Fresh Avahi file inspection additionally found `/usr/share/dbus-1/system-services/org.freedesktop.Avahi.service` with `SystemdService=dbus-org.freedesktop.Avahi.service` and `Exec=/bin/false`; the installed alias symlink targets the canonical service. This establishes the observed activation routing, not running state.

### Platform documentation and compatibility
- [zram-generator config manual](https://github.com/systemd/zram-generator/blob/main/man/zram-generator.conf.md): default expression is `min(ram / 2, 4096)` with MiB units and priority 100; supports drop-ins. Consult installed 1.2.1 manual before rendering. Choose this established capped policy rather than source's uncapped ~31 GiB device. lz4 remains a source candidate selected only after kernel support check. No automatic active-device restart.
- [Linux zram](https://docs.kernel.org/admin-guide/blockdev/zram.html): device compression capabilities and memory statistics are observable through sysfs; logical size is not reserved physical memory. Algorithm availability still requires host verification.
- [Linux VM sysctls](https://www.kernel.org/doc/html/latest/admin-guide/sysctl/vm.html): reclaim costs depend on storage and workload. Mixed disk/zram swap justifies retaining existing reclaim rather than importing all-RAM-cost assumptions. Dirty byte and ratio controls interact; retain both unchanged.
- [earlyoom manual](https://github.com/rfjakob/earlyoom/blob/master/MANPAGE.md), fetched through plugin: RAM and aggregate free-swap thresholds are jointly required; `--avoid` subtracts 300, `--prefer` adds 300, regex uses first 15 bytes of comm; `--dryrun` does not kill. The installed version must be checked before enabling.
- [systemd 259 tmpfiles](https://www.freedesktop.org/software/systemd/man/259/tmpfiles.d.html): owner-requested `w` line targets existing sysfs attribute; detect conflicting tmpfiles entries as well as missing interface.
- [journald](https://www.freedesktop.org/software/systemd/man/latest/journald.conf.html), [coredump](https://www.freedesktop.org/software/systemd/man/latest/coredump.conf.html): merged drop-ins and handler routing matter; retention settings are not strict instantaneous disk quotas. Latest documentation is newer than host 259; use installed manuals for effective semantics. Preserve other handlers; do not install coredump solely to replace Apport.
- [systemd 259 systemctl](https://www.freedesktop.org/software/systemd/man/259/systemctl.html): disabling a unit alone does not prevent other activation; masking and installed activation aliases need review.
- [Linux network sysctls](https://docs.kernel.org/networking/ip-sysctl.html): TCP knobs are workload-dependent, so absence of laptop network measurements leads to rejecting managed overrides.
- [intel_pstate](https://docs.kernel.org/admin-guide/pm/intel_pstate.html): no_turbo controls runtime turbo permission; preserve existing driver and boot arguments.

## Architecture Pattern Evaluation

| Option | Strength | Risk | Decision |
|---|---|---|---|
| Copy three source modules unchanged | Small initial port | Active swap recreation, destructive service/boot changes | Reject |
| Optional feature entry with native drop-ins | Fits current pyinfra; isolated ownership and rollback | Requires preflight and host validation | Adopt |
| New resource agent/daemon | Central policy loop | Unnecessary service and duplicate platform behavior | Reject |

## Design Decisions

### Decision: platform drop-ins with captured baselines
Use native tmpfiles, generator, earlyoom and systemd drop-ins. Share only a typed preflight/report/backup contract; each policy component owns distinct artifacts. This generalizes restoration without inventing a daemon or policy framework. Existing foundation execution/package policy remains upstream; no root deploy changes in this spec.

### Decision: conservative memory and developer policy
Use the generator's capped 4096 MiB policy with source lz4/priority 100 when available. At ~62.7 GiB this supplies a modest compressed tier while preserving 16 GiB disk swap and resume configuration. Retain swappiness60 and page-cluster3 because disk swap remains. Earlyoom retains source 5% RAM /10% aggregate free swap and hourly reporting, with desktop avoidance extended to observed Plasma/KWin names. At this RAM size 5% is roughly 3 GiB, but installed v1.8+ uses dynamic userspace-total accounting; do not promise a fixed reserve or kernel-OOM prevention. Reject forced preference for every source browser/electron process because no laptop workload evidence establishes that sacrificing those apps is desirable. Existing competing OOM policy blocks new killer activation until separately reconciled.

### Decision: tuning values are individually assessed
The complete adopt/reject matrix is in design.md. Only the development inotify-instance floor 1024 is newly adopted; current 128 can constrain concurrently active IDE/dev-tool watchers. Preserve higher limits. Existing watches 559994 already exceed source524288, so no watches override. Reject network/reclaim/durability tuning without demonstrated laptop benefit. This is an explicit port disposition, not silent omission or a performance claim.

### Decision: preserve services, block Avahi activation
Preserve Bluetooth, existing power management, CUPS and ModemManager states. Stop/mask installed Avahi service/socket and resolve D-Bus aliases/activation metadata before claiming disabled. Direct-address printing remains possible; unknown printer details do not block this policy. Preserve preexisting masks and package ownership during rollback.

## Risks & Mitigations
- System bus unavailable in this session: runtime service baseline, collision discovery and application are implementation-time gates; no service states inferred.
- Existing swap/OOM managers or later overrides: detect and block only affected component, allow independent planning/status.
- Hibernation resume state incomplete: retain all settings/devices and validate readable metadata; no capacity guarantee or new setup.
- Source “never kill” wording inaccurate: document avoidance semantics and test comm truncation.
- Storage settings permit temporary overshoot/active files: validate effective directives and expected retention semantics rather than assert instantaneous hard quotas.
- Privileged operations and reboot/pressure tests are planned, not executed during spec work.

## References
Pinned source asset links use the tree [files/system](https://github.com/norandom/hyperland-forky-worker-vm/tree/a1c09ec3f02a98b7c6a4641f907108a2ad080993/files/system). Local context and official contracts are linked in the research entries above. No secondary tuning advice or source performance claims were treated as host measurements.

### Fresh-install audio clarification
Read `.kiro/steering/desktop-audio-policy.md` after parent relayed the owner clarification. Preserve apple-t2-audio-config ALSA UCM profiles, PipeWire/WirePlumber and Bluetooth audio. Resource service policy does not start Plasma inside Hyprland, remove audio support or import VM audio routing. Audio runtime behavior remains unverified; no new task seam is needed because preservation belongs to existing LaptopServices.

### Cross-spec guarded-package contract correction
Cross-review found undefined foundation no-autostart support in the resource design. Parent's foundation amendment supplies `install_packages(request: PackageRequest, *, prevent_service_start: bool = False) -> None`, implemented by foundation task 2.4. Resource design/task 1.3 explicitly consume `install_packages(request, prevent_service_start=True)` after that prerequisite. Foundation owns the temporary deny-all policy-rc.d transaction, preserves known deny policy unchanged, rejects unrecognized/conflicting policy before mutation, and restores owned temporary state on failure using journal recovery. Startup suppression leaves protected maintainer-hook and no-go checks independently mandatory. Rechecked all 26 acceptance criteria against design/task mappings after the narrow consumer amendment; none are missing or invalid. This records a specification contract, not runtime verification.
