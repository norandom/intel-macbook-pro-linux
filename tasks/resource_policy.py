"""Laptop resource policy, ported from the worker VM's memory/tuning/services tasks.

Adopted: turbo off at boot + turbo aliases fragment, additive capped zram (disk swap and
resume untouched), earlyoom aware of KDE and Hyprland, journald/coredump size limits,
inotify instances floor, Avahi masked. Rejected (see .kiro/specs/laptop-resource-policy/
design.md): reclaim/dirty/network sysctls, nofile, /tmp size, noatime, watchdog, GRUB
cmdline, serial console, root SSH, module blacklist, qemu agent, away lock, snitch.
GPU power settings are intentionally not touched here.
"""
import os
from io import StringIO
from pathlib import Path

from pyinfra import local, logger
from pyinfra.operations import files, server, systemd

from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage import resource_policy as rp
from manage.userconfig import setting

validate_local_context()
local.include("tasks/package_policy.py")

HERE = Path(__file__).resolve().parents[1] / "files/resource-policy"
home = os.path.expanduser("~")

install_packages(PackageRequest(packages=("systemd-zram-generator", "earlyoom"), source="ubuntu"))

# --- Turbo: off at boot; aliases in a fragment shell-user-tools sources ---------------------
turbo_rule = files.put(
    name="tmpfiles: intel_pstate no_turbo=1 at boot",
    src=str(HERE / "no-turbo.conf"),
    dest="/etc/tmpfiles.d/no-turbo.conf",
    user="root", group="root", mode="644",
    _sudo=True,
)
if os.path.exists(rp.TURBO_SYSFS):
    server.shell(
        name="Apply no_turbo now and verify readback",
        commands=["systemd-tmpfiles --create /etc/tmpfiles.d/no-turbo.conf",
                  f"test \"$(cat {rp.TURBO_SYSFS})\" = 1"],
        _sudo=True,
        _if=turbo_rule.did_change,
    )
else:
    logger.warning(f"resource-policy: {rp.TURBO_SYSFS} absent; boot rule staged, turbo not verified")

files.directory(name="~/.config/t2-mac-kde", path=f"{home}/.config/t2-mac-kde", mode="755")
files.put(
    name=f"turbo-on/off/status alias fragment ({rp.TURBO_FRAGMENT})",
    src=str(HERE / "turbo.bash"),
    dest=f"{home}/.config/t2-mac-kde/turbo.bash",
    mode="644",
)

# --- zram: additive, priority 100 over disk swap (-1); active swap is never torn down --------------
zram_conflict = [u for u in ("zramswap.service", "zram-config.service")
                 if rp.unit_installed(rp.unit_state(u))]
if zram_conflict:
    logger.warning(f"resource-policy: other zram manager {zram_conflict}; zram policy skipped")
else:
    zram = files.put(
        name="zram swap: min(ram/2, 4096M), lz4, priority 100",
        src=str(HERE / "zram-generator.conf"),
        dest="/etc/systemd/zram-generator.conf.d/60-t2-resource.conf",
        user="root", group="root", mode="644",
        _sudo=True,
    )
    # Only bring up a fresh device; an existing zram0 picks up changes at next boot.
    server.shell(
        name="daemon-reload; start zram0 only if no zram device exists yet",
        commands=["systemctl daemon-reload",
                  "if [ ! -e /dev/zram0 ]; then systemctl start systemd-zram-setup@zram0.service; fi"],
        _sudo=True,
        _if=zram.did_change,
    )

# --- earlyoom: desktop-aware avoid list, no browser preference -------------------------------
oom_conflict = [u for u in ("systemd-oomd.service", "nohang.service", "nohang-desktop.service")
                if rp.unit_active(u)]
eo = files.put(
    name="earlyoom args: -m 5 -s 10, avoid KDE/Hyprland session stack",
    src=StringIO(rp.earlyoom_defaults()),
    dest="/etc/default/earlyoom",
    user="root", group="root", mode="644",
    _sudo=True,
)
if oom_conflict:
    logger.warning(f"resource-policy: {oom_conflict} active; earlyoom configured but not enabled")
else:
    systemd.service(name="earlyoom enabled and running", service="earlyoom.service",
                    running=True, enabled=True, restarted=eo.did_change, _sudo=True)

# --- Diagnostics: journald and (if active handler) systemd-coredump limits -----------------
jd = files.put(
    name="journald: SystemMaxUse=500M RuntimeMaxUse=100M",
    src=str(HERE / "journald.conf"),
    dest="/etc/systemd/journald.conf.d/60-t2-resource.conf",
    user="root", group="root", mode="644",
    _sudo=True,
)
systemd.service(name="Restart journald (config changed)", service="systemd-journald.service",
                restarted=True, _sudo=True, _if=jd.did_change)

coredump_on = rp.coredump_applicable(rp.read_text("/proc/sys/kernel/core_pattern"))
if coredump_on:
    files.put(
        name="coredump: MaxUse=500M KeepFree=1G",
        src=str(HERE / "coredump.conf"),
        dest="/etc/systemd/coredump.conf.d/60-t2-resource.conf",
        user="root", group="root", mode="644",
        _sudo=True,
    )
else:
    logger.warning("resource-policy: systemd-coredump is not the crash handler; core limits inapplicable")
    files.file(name="coredump limits inapplicable: no managed drop-in",
               path="/etc/systemd/coredump.conf.d/60-t2-resource.conf", present=False, _sudo=True)

# --- Development limits: inotify instances floor (never lowers a larger value) -------------
current = rp.read_int("/proc/sys/fs/inotify/max_user_instances")
limits = files.put(
    name=f"sysctl fs.inotify.max_user_instances >= {rp.INOTIFY_INSTANCES_FLOOR}",
    src=StringIO(rp.limits_sysctl(current)),
    dest="/etc/sysctl.d/60-t2-resource-limits.conf",
    user="root", group="root", mode="644",
    _sudo=True,
)
server.shell(name="Apply only the managed sysctl file",
             commands=["sysctl -p /etc/sysctl.d/60-t2-resource-limits.conf"],
             _sudo=True, _if=limits.did_change)

# --- Services: Avahi off (service + socket masked; D-Bus activation routes via the
#     masked alias). Bluetooth, CUPS, power, ModemManager, audio stay untouched.
#     Printing still works by direct IP/hostname; mDNS discovery is gone. ---------------------
avahi = [u for u in ("avahi-daemon.socket", "avahi-daemon.service")
         if rp.unit_installed(rp.unit_state(u)) and rp.unit_state(u) != "masked"]
if avahi:
    server.shell(
        name=f"Stop and mask {' '.join(avahi)}",
        commands=[f"systemctl disable --now {' '.join(avahi)}", f"systemctl mask {' '.join(avahi)}"],
        _sudo=True,
    )

# --- Crash report upload (config crash_upload; Ubuntu default: on) ------------------------
# Off: whoopsie (uploads apport reports to errors.ubuntu.com) stopped and masked, and its
# start-limit failures after crash bursts are cleared. Local capture stays (systemd-coredump /
# coredumpctl). On again: unmasked. Plain systemctl state, so it is fully revertable.
WHOOPSIE = ("whoopsie.path", "whoopsie.service")
upload = bool(setting("crash_upload", True))
installed = [u for u in WHOOPSIE if rp.unit_installed(rp.unit_state(u))]
if installed and not upload and any(rp.unit_state(u) != "masked" for u in installed):
    server.shell(name=f"Crash upload off: stop and mask {' '.join(installed)}", _sudo=True, commands=[
        f"systemctl stop {' '.join(installed)}", f"systemctl mask {' '.join(installed)}",
        f"systemctl reset-failed {' '.join(installed)} || true"])
elif installed and upload and any(rp.unit_state(u) == "masked" for u in installed):
    server.shell(name=f"Crash upload on: unmask {' '.join(installed)}", _sudo=True, commands=[
        f"systemctl unmask {' '.join(installed)}", "systemctl enable --now whoopsie.path"])

# --- Power tuning (config power_tuning; owner request 2026-11-16, measured with powertop) -----
# Selective, reversible: three safe Intel chipset functions get runtime PM, two sysctls cut
# wakeups. T2 devices, Apple NVMe, Wi-Fi, the SMC's LPC bridge and PCIe ASPM stay untouched.
install_packages(PackageRequest(packages=("powertop",)))
tuning = bool(setting("power_tuning", False))
pci_rule = files.put(name=f"udev: PCI runtime PM for 3 Intel chipset functions ({'on' if tuning else 'off'})",
                     src=str(Path(__file__).resolve().parents[1] / "files/resource-policy/62-t2-pci-runtime-pm.rules"),
                     dest="/etc/udev/rules.d/62-t2-pci-runtime-pm.rules", mode="644", _sudo=True) \
    if tuning else files.file(name="udev: PCI runtime PM rule removed (power_tuning off)",
                              path="/etc/udev/rules.d/62-t2-pci-runtime-pm.rules", present=False, _sudo=True)
power_conf = files.put(name="sysctl: fewer wakeups (nmi_watchdog off, writeback 15 s)",
                       src=str(Path(__file__).resolve().parents[1] / "files/resource-policy/62-t2-power.conf"),
                       dest="/etc/sysctl.d/62-t2-power.conf", mode="644", _sudo=True) \
    if tuning else files.file(name="sysctl: power tuning removed (power_tuning off)",
                              path="/etc/sysctl.d/62-t2-power.conf", present=False, _sudo=True)
server.shell(name="Apply power tuning now (udev + sysctl; reverting needs a reboot for the sysctls)",
             _if=lambda: pci_rule.did_change() or power_conf.did_change(), _sudo=True,
             commands=["udevadm control --reload", "udevadm trigger --subsystem-match=pci --action=change",
                       "sysctl -p /etc/sysctl.d/62-t2-power.conf 2>/dev/null || true"])
