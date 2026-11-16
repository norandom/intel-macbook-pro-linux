# CPU security mitigations off (config flag)

The kernel protects against the Spectre/Meltdown family of CPU flaws (Spectre v1/v2, MDS/MMIO
buffer clearing, Retbleed, BHI, ...) with extra work on kernel entry and exit, context switches
and some branches. The owner's call (2026-11-16): single-user workstation, performance first,
so turn them off with one kernel option, `mitigations=off`.


## What to expect

Measure rather than assume. The baseline already shows the mitigations are fairly cheap on this
i9-9980HK: a syscall costs about 0.16 µs (`docs/benchmark.md`). Typical gains with
`mitigations=off` on this CPU generation are small for desktop work and a few to ~15 % for
syscall- and context-switch-heavy work (builds, many short processes, heavy I/O, VMs).

## What stays exposed

These flaws let code on this machine read memory it shouldn't. With one user, that means code
you run yourself: JavaScript in browsers (browsers keep their own mitigations: site isolation,
coarse timers), the npm/pip/cargo packages you install (Safe Chain checks them before install),
and the guests under KVM/libvirt reading host memory. Nothing becomes reachable from the
network by this change.

## Order: before, macOS, after

1. **Before** (done 2026-11-16): `benchmarks/linux.json`, Linux with mitigations on, AC,
   turbo off, balanced, 10 runs.
2. **macOS** (done 2026-11-16) on the same Mac: `benchmarks/macos.json` (turbo off via Turbo Boost Switcher,
   Low Power Mode off). macOS keeps its mitigations on, so this compares against step 1.
3. **After**: set the flag and deploy (below), reboot, then
   `benchmarks/mitigations-off/linux.json` under the same conditions as step 1.

Three comparisons then come out of `tools/benchmark-compare.sh`:

```sh
bash tools/benchmark-compare.sh benchmarks/linux.json benchmarks/macos.json                       # Linux vs macOS, both mitigated
bash tools/benchmark-compare.sh benchmarks/linux.json benchmarks/mitigations-off/linux.json      # cost of the mitigations
bash tools/benchmark-compare.sh benchmarks/macos.json benchmarks/mitigations-off/linux.json      # macOS vs tuned Linux
```

## Do it

Set the flag in `~/.config/t2-mac-kde/config.toml` and deploy (part of `deploy.py`, or alone):

```toml
cpu_mitigations_off = true
```

```sh
.venv/bin/pyinfra @local tasks/cpu_mitigations.py --use-sudo-password
```

The task writes one GRUB drop-in, `/etc/default/grub.d/90-t2-mitigations.cfg`, which appends
`mitigations=off` to the kernel options; `/etc/default/grub` itself stays as it is. Only when
the drop-in changes does it back up `/boot/grub/grub.cfg` (to `grub.cfg.before-t2-mitigations`)
and run `update-grub`, the same regeneration every kernel update performs. Kernels, initramfs
and LUKS aren't touched. Each deploy also checks that the boot menu matches the setting, so a
failed `update-grub` is retried. The backup always holds the menu from just before the last
change. It takes effect at the next reboot; until then new shells print
`t2: CPU mitigations off is configured - reboot to apply`.

This is the one owner-approved exception to the protected boot boundary
(`.kiro/steering/protected-system-boundary.md`).

## Check and measure

```sh
grep mitigations=off /proc/cmdline
grep . /sys/devices/system/cpu/vulnerabilities/*        # now mostly "Vulnerable"
bash tools/benchmark.sh --runs 10 --json --out benchmarks/mitigations-off
bash tools/benchmark-compare.sh benchmarks/linux.json benchmarks/mitigations-off/linux.json
```

Use the same conditions as the baseline (AC, turbo off, balanced, machine idle). The kernel
rows (syscall, stat, pipe, fork, spawn) show the effect; the CPU rows should stay the same.
If the gain is negligible, going back costs nothing.

## Going back

If the system misbehaves after the reboot, the GRUB menu's recovery entry boots without the
option (the menu is hidden: hold **Shift** or tap **Esc** right after the Apple chime).


Set `cpu_mitigations_off = false` (or remove the line), run the task again and reboot. It
removes the drop-in and regenerates the boot menu. By hand, without the repo:

```sh
sudo rm /etc/default/grub.d/90-t2-mitigations.cfg && sudo update-grub
```
