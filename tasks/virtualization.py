"""virt-manager on KVM: owner builds their own VMs on libvirt's default NAT ("shared") network.

Guests reach the internet through the host: directly, or via the Tailscale exit node when
it is switched on in the tray (libvirt masquerades into whatever route the host uses), with
LAN access kept (`--exit-node-allow-lan-access`, tasks/remote_access.py). KVM (kvm_intel) is
already part of the running kernel; nothing here touches kernel, boot or storage.
"""
import os
import pwd

from pyinfra import host
from pyinfra.facts.server import Command
from io import StringIO

from pyinfra.operations import files, server, systemd
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context

validate_local_context()
user = pwd.getpwuid(os.getuid()).pw_name

install_packages(PackageRequest(packages=(
    "qemu-system-x86", "qemu-utils", "libvirt-daemon-system", "libvirt-clients",
    "virt-manager", "virt-viewer", "ovmf", "swtpm", "swtpm-tools", "dnsmasq-base",
)))

systemd.service(name="libvirtd socket at boot", service="libvirtd.socket", running=True, enabled=True, _sudo=True)
server.shell(
    name=f"{user} in the libvirt group (takes effect at next login)",
    commands=[f"usermod -aG libvirt {user}"],
    _if=lambda: user not in (host.get_fact(Command, command="id -nG") or "").split(),
    _sudo=True,
)
server.shell(
    name="libvirt default NAT network: defined, autostarted, running",
    commands=["virsh -c qemu:///system net-info default >/dev/null 2>&1 || "
              "virsh -c qemu:///system net-define /usr/share/libvirt/networks/default.xml",
              "virsh -c qemu:///system net-autostart default",
              "virsh -c qemu:///system net-info default | grep -q '^Active:.*yes' || "
              "virsh -c qemu:///system net-start default"],
    _sudo=True,
)

# Nested virtualization: kvm_intel nested=Y is already the kernel default (read-only at
# runtime; nothing to change). Windows guests (especially nested Hyper-V/WSL2) can crash on
# unknown MSR accesses: let KVM ignore them, without log spam. Runtime module parameters
# set via tmpfiles.d (like no-turbo) - no modprobe.d, no initramfs, no module reload.
kvm_msrs = files.put(
    name="KVM: ignore unknown guest MSRs (Windows guests), don't log them",
    src=StringIO("# Managed by t2-mac-kde (virtualization)\n"
                 "w /sys/module/kvm/parameters/ignore_msrs - - - - Y\n"
                 "w /sys/module/kvm/parameters/report_ignored_msrs - - - - N\n"),
    dest="/etc/tmpfiles.d/t2-kvm-msrs.conf", mode="644", _sudo=True,
)
server.shell(name="Apply KVM MSR settings now", commands=["systemd-tmpfiles --create /etc/tmpfiles.d/t2-kvm-msrs.conf"],
             _if=kvm_msrs.did_change, _sudo=True)
