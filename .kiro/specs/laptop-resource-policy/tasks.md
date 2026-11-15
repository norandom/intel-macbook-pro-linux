# Implementation Checklist: laptop-resource-policy

Entry point: `tasks/resource_policy.py` (helpers `manage/resource_policy.py`, assets `files/resource-policy/`,
tests `tests/test_resource_policy.py`). Ported from source `tasks/memory.py`, `tuning.py`, `services.py`, `away.py`.

## Implemented
- [x] Packages `systemd-zram-generator`, `earlyoom` via `install_packages(PackageRequest(..., source="ubuntu"))`.
- [x] Turbo boot default: `/etc/tmpfiles.d/no-turbo.conf` (exact rule); applied with `systemd-tmpfiles --create` + readback when changed; warns if sysfs is absent.
- [x] Turbo aliases fragment at stable path `~/.config/t2-mac-kde/turbo.bash` (exact three aliases, 0644, user-owned). No shell startup file is edited; shell-user-tools sources it.
- [x] zram drop-in `/etc/systemd/zram-generator.conf.d/60-t2-resource.conf`: `min(ram / 2, 4096)`, lz4, priority 100 (> disk swap -1). daemon-reload; zram0 started only when no zram device exists. No swapoff/mkswap/fstab/resume changes. Skipped with warning if zramswap/zram-config present.
- [x] earlyoom `/etc/default/earlyoom`: source `-m 5 -s 10 -r 3600`; `--avoid` built from escaped 15-char comm names for KDE/Plasma/KWin/SDDM and Hyprland stacks plus PipeWire; source browser `--prefer` rejected. Not enabled if systemd-oomd/nohang is active. Restart only on change.
- [x] journald drop-in `60-t2-resource.conf` (SystemMaxUse=500M, RuntimeMaxUse=100M); journald restart only on change.
- [x] coredump drop-in (MaxUse=500M, KeepFree=1G) only when `core_pattern` uses systemd-coredump; otherwise removed and reported as not applicable.
- [x] `fs.inotify.max_user_instances` floor 1024 (never lowers a larger value) in `/etc/sysctl.d/60-t2-resource-limits.conf`; only that file is applied.
- [x] Avahi: `avahi-daemon.socket`/`.service` disabled, stopped and masked when installed and not already masked (the D-Bus activation goes through the masked alias). Bluetooth, CUPS, power, ModemManager and audio are left alone. Printing still works with a direct IP/hostname; mDNS discovery stops working.
- [x] Rejected source tuning (design.md table): swappiness, vfs_cache_pressure, page-cluster, watermarks, dirty_*, max_user_watches, nofile, watchdog, all network sysctls/BBR, /tmp size, noatime/commit, GRUB cmdline, serial console, root SSH, module blacklist, qemu agent, hypr-away, snitch.
- [x] Unit tests: exact turbo assets, zram settings, no teardown/boot ops, avoid regex coverage, 15-char limit, inotify floor, coredump applicability.

## Deferred / needs live owner check
- [ ] Live deploy (needs sudo): run `pyinfra @local tasks/resource_policy.py` as owner.
- [ ] After apply/reboot: `swapon --show` shows zram0 prio 100 and dm-1 still prio -1; `zramctl` reports lz4.
- [ ] `earlyoom --dryrun` style check of avoid list in both KDE and Hyprland sessions (Hyprland comm names unobserved yet).
- [ ] Confirm Avahi stays down after a socket/D-Bus activation attempt; confirm CUPS direct-address printing.
- [ ] Not implemented (ceremony): snapshot manifests/restore tooling; restore is by deleting the managed drop-ins and running `systemctl unmask avahi-daemon.socket avahi-daemon.service`.
- [ ] GPU power configuration: out of scope here, pending capture.
