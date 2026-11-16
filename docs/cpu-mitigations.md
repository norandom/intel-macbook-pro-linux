# CPU security mitigations off (owner-run)

The kernel protects against the Spectre/Meltdown family of CPU flaws (Spectre v1/v2, MDS/MMIO
buffer clearing, Retbleed, BHI, ...) with extra work on kernel entry and exit, context switches
and some branches. The owner's call (2026-11-16): single-user workstation, performance first,
so turn them off with one kernel option, `mitigations=off`.

It's a kernel command-line change in `/etc/default/grub`, which is on the protected list
(`.kiro/steering/protected-system-boundary.md`), so it's a manual step, not part of the deploy.

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

## Do it

```sh
sudo cp /etc/default/grub /etc/default/grub.before-mitigations
sudoedit /etc/default/grub
```

Add `mitigations=off` to the existing line, keeping everything else:

```
GRUB_CMDLINE_LINUX_DEFAULT='quiet splash intel_iommu=on iommu=pt pm_async=off mitigations=off'
```

Then `sudo update-grub` and reboot. The initramfs doesn't need regenerating. (If you also want
verbose boot from `docs/verbose-boot.md` later, it's the same line: drop `quiet splash`.)

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

```sh
sudo cp /etc/default/grub.before-mitigations /etc/default/grub && sudo update-grub
```
