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
from pyinfra.operations import server, systemd
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
