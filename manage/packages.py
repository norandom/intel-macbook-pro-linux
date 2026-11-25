"""Guarded apt installs for the desktop deploy.

Rules (see .kiro/steering/package-policy.md, protected-system-boundary.md):
- no Snap/snapd/Flatpak, no protected (kernel/boot/storage/T2/audio) packages,
  requested or pulled in transitively;
- no removals; dependency upgrades only for non-protected packages;
- before apt runs as root, every planned .deb is downloaded and inspected:
  payload paths and maintainer scripts/triggers must not touch the protected
  boot/storage boundary (initramfs, grub, kernel modules, cryptsetup, ...).

Preview (unprivileged, `apt-get --simulate`) decides whether an operation is
scheduled at all; the sudo helper re-runs every check right before installing.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
from typing import Literal


@dataclass(frozen=True)
class PackageRequest:
    packages: tuple[str, ...]
    source: Literal["ubuntu"] = "ubuntu"
    # The only removals a request may cause: installed packages that conflict with what it
    # installs, named here one by one (e.g. the legacy libappindicator3 stack that Ubuntu's
    # Ayatana packages replace). Any other removal still blocks the plan.
    replaces: tuple[str, ...] = ()


@dataclass(frozen=True)
class PackagePlan:
    installs: tuple[tuple[str, str], ...]
    removals: tuple[str, ...] = ()


_ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C", "LANG": "C"}
_NAME = re.compile(r"[a-z0-9][a-z0-9+.-]+(?::[a-z0-9][a-z0-9-]*)?(?:=[0-9][a-zA-Z0-9.+:~\-]*)?\Z")
_FORBIDDEN = re.compile(r"^(?:snapd?$|flatpak$|snapd-|flatpak-|libflatpak|libsnapd)|-(?:plugin|backend)-(?:snap|flatpak)$")
_PROTECTED = re.compile(
    r"(?:linux(?:-|$)|grub|shim|efibootmgr|systemd-boot|ukify|kernel-install|initramfs|mkinit|dracut"
    r"|cryptsetup|lvm|libcryptsetup|libdevmapper|liblvm|dmsetup|thin-provisioning|dkms|kmod"
    r"|udev$|systemd$|firmware|apple-|t2-|pipewire|wireplumber|alsa-ucm|alsa-base)")
_PROTECTED_PATHS = (
    "/boot/", "/lib/modules/", "/usr/lib/modules/", "/usr/src/", "/etc/fstab", "/etc/crypttab",
    "/etc/cryptsetup", "/usr/lib/cryptsetup", "/etc/lvm/", "/etc/initramfs-tools/",
    "/usr/share/initramfs-tools/", "/etc/mkinitcpio", "/etc/dracut", "/usr/lib/dracut/",
    "/etc/default/grub", "/etc/grub.d/", "/usr/lib/grub/", "/etc/kernel/", "/usr/lib/kernel/",
    "/etc/modprobe.d/", "/usr/lib/modprobe.d/", "/etc/modules-load.d/", "/usr/lib/modules-load.d/",
    "/lib/firmware/", "/usr/lib/firmware/",
    "/usr/lib/initramfs-tools/", "/usr/lib/initcpio/", "/usr/share/initcpio/", "/etc/initcpio/",
    "/usr/lib/mkinitcpio/", "/usr/share/mkinitcpio/", "/usr/share/grub/", "/usr/lib/shim/",
    "/usr/lib/systemd/boot/", "/usr/lib/systemd/ukify", "/usr/bin/bootctl", "/usr/bin/kernel-install",
    "/usr/bin/efibootmgr", "/usr/sbin/efibootmgr", "/usr/bin/grub-", "/usr/sbin/grub-", "/usr/sbin/update-grub",
    "/usr/sbin/update-initramfs", "/usr/bin/mkinitcpio", "/usr/sbin/mkinitcpio", "/usr/bin/dracut",
    "/usr/sbin/cryptsetup", "/usr/sbin/lvm",
)
_PROTECTED_LIBRARY = re.compile(r"/usr/lib(?:32|64)?/(?:[^/]+/)*(?:libcryptsetup|libdevmapper|liblvm)[^/]*$")
_PROTECTED_SCRIPT = re.compile(
    rb"update-initramfs|mkinitcpio|dracut|update-grub|grub-install|grub-mkconfig|cryptsetup|"
    rb"depmod|dkms|kernel-install|"
    # kernel modules: building or loading out-of-tree ones and unloading drivers (2026-11-16:
    # VTune's postinst runs sepdk build-driver + insmod via a boot script). A plain
    # `modprobe <name>` (in-tree module, e.g. fuse3) and modprobe.d paths stay allowed.
    rb"\binsmod\b|\brmmod\b|\bmodprobe\b[^\n;|&]*\s(?:-[a-zA-Z]*[rd][a-zA-Z]*|--remove|--dirname)\b|"
    rb"build-driver|/lib/modules/|\.ko(?:\.(?:xz|zst|gz))?\b|/usr/src/linux|\bmake\b[^\n;|&]*\sM=")
_MAX_PACKAGES = 256
# Vendor .deb files (pinned + sha256-checked by their task) are staged here and passed
# to the root helper by absolute path; the guard scans them like archive packages.
LOCAL_DEBS = Path("/var/cache/t2-mac-kde/debs")
_LOCAL_DEB = re.compile(r"/var/cache/t2-mac-kde/debs/[A-Za-z0-9][A-Za-z0-9+._~-]*\.deb\Z")


def _protected(name: str) -> bool:
    return bool(_FORBIDDEN.search(name) or _PROTECTED.match(name))


def validate_request(request: PackageRequest) -> None:
    if (not isinstance(request, PackageRequest) or not isinstance(request.packages, tuple)
            or not 0 < len(request.packages) <= _MAX_PACKAGES):
        raise RuntimeError("A nonempty tuple of package names is required.")
    if len({p.split("=")[0].split(":")[0] for p in request.packages}) != len(request.packages):
        raise RuntimeError("Duplicate package selections are not allowed.")
    for package in request.packages:
        if isinstance(package, str) and _LOCAL_DEB.match(package):
            continue  # name checked from the plan (Inst lines) and the archive scan
        if not isinstance(package, str) or not _NAME.match(package):
            raise RuntimeError(f"Invalid package selection: {package!r}")
        if _protected(package.split("=")[0].split(":")[0]):
            raise RuntimeError(f"Prohibited or protected package: {package}")
    if not isinstance(request.replaces, tuple) or len(request.replaces) > 8:
        raise RuntimeError("replaces must be a tuple of at most 8 package names.")
    for package in request.replaces:
        if not isinstance(package, str) or not _NAME.match(package) or "=" in package or package.endswith("-"):
            raise RuntimeError(f"Invalid replaced package: {package!r}")
        if _protected(package.split(":")[0]):
            raise RuntimeError(f"Protected package cannot be replaced: {package}")
        if package in request.packages:
            raise RuntimeError(f"Package both installed and replaced: {package}")


def _run(argv) -> str:
    result = subprocess.run(argv, env=_ENV, capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise RuntimeError(f"{argv[0]} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def _wanted(request) -> tuple[str, ...]:
    """The selections apt still has to act on. A plain name that is already installed is left
    out: "apt-get install <installed>" upgrades it to the candidate, and with it every package
    that must match its version (2026-11-25: the speaker DSP plugins pulled a PipeWire update
    from resolute-updates). Updates stay manual. Pinned "name=version" and staged .debs stay in."""
    return tuple(p for p in request.packages
                 if _LOCAL_DEB.match(p) or "=" in p or not _installed(p))


def _apt_args(request):
    # Lock::Timeout: apt waits (instead of failing) if a background apt run takes the lock between
    # the transaction's lock check and this call.
    # Named replacements are removed explicitly ("name-"), so --no-remove is dropped only then;
    # the simulation still allows no removal beyond them.
    replaced = tuple(f"{p}-" for p in request.replaces if _installed(p))
    wanted = _wanted(request)
    if not (wanted or replaced):
        return None   # everything is installed: nothing for apt to do
    return ("/usr/bin/apt-get", "-o", "DPkg::Lock::Timeout=300", "--no-install-recommends",
            *(() if replaced else ("--no-remove",)), "install", *wanted, *replaced)


def _installed(package: str) -> bool:
    result = subprocess.run(("/usr/bin/dpkg-query", "-W", "-f=${db:Status-Status}", package),
                            env=_ENV, capture_output=True, text=True, timeout=10)
    return result.returncode == 0 and result.stdout == "installed"


def _parse_simulation(output: str, allowed_removals: tuple[str, ...] = ()) -> PackagePlan:
    installs, removals = [], []
    for line in output.splitlines():
        if line.startswith("Remv "):
            removals.append(line.split()[1])
            continue
        match = re.match(r"Inst (\S+)( \[[^\]]+\])? \((\S+)", line)
        if not match:
            continue
        package, _previous, version = match.groups()
        name = package.split(":")[0]
        if _protected(name):
            raise RuntimeError(f"Plan would install/upgrade protected or prohibited package {package}; blocked.")
        installs.append((package, version))
    blocked = [r for r in removals if r not in allowed_removals and r.split(":")[0] not in allowed_removals]
    if blocked:
        raise RuntimeError(f"Plan would remove packages {blocked}; blocked.")
    return PackagePlan(tuple(installs), tuple(removals))


def inspect_plan(request: PackageRequest) -> PackagePlan:
    """Unprivileged apt simulation of exactly this request."""
    validate_request(request)
    argv = _apt_args(request)
    if argv is None:
        return PackagePlan((), ())
    try:
        output = _run((argv[0], "--simulate", *argv[1:]))
    except RuntimeError as error:
        if "remove is disabled" not in str(error):
            raise
        # Name the packages apt wants to remove (blocked below) instead of apt's bare refusal.
        output = _run((argv[0], "--simulate", *(a for a in argv[1:] if a != "--no-remove")))
    return _parse_simulation(output, request.replaces)


# Replacements requested earlier in this deploy run. pyinfra plans every task before it runs
# any, so a later task's simulation must already assume them (e.g. tasks/apps.py installing
# nm-applet, which needs the Ayatana library that tasks/dev_libs.py swaps in).
_PENDING_REPLACES: set[str] = set()


def _with_pending(request: PackageRequest) -> PackageRequest:
    _PENDING_REPLACES.update(request.replaces)
    extra = tuple(sorted(p for p in _PENDING_REPLACES if p not in request.replaces and p not in request.packages))
    return request if not extra else PackageRequest(request.packages, request.source, request.replaces + extra)


def _local_deb(package: str, version: str, request: PackageRequest) -> Path | None:
    for candidate in request.packages:
        if _LOCAL_DEB.match(candidate):
            fields = _run(("/usr/bin/dpkg-deb", "--field", candidate, "Package", "Version")).split("\n")
            if fields[0].split(": ", 1)[-1] == package.split(":")[0] and fields[1].split(": ", 1)[-1] == version:
                return Path(candidate)
    return None


def _native_arch() -> str:
    return _run(("/usr/bin/dpkg", "--print-architecture")).strip()


def _deb_path(package: str, version: str) -> Path:
    # apt names native packages without ":arch"; with multiarch (wine32:i386) the same
    # name and version can also be cached as _i386.deb, so the native arch must be explicit.
    name, _, arch = package.partition(":")
    arch = arch or _native_arch()
    pattern = f"{name}_{version.replace(':', '%3a')}_"
    matches = [p for p in Path("/var/cache/apt/archives").glob(pattern + "*.deb")
               if not arch or p.name.endswith(f"_{arch}.deb") or p.name.endswith("_all.deb")]
    if len(matches) != 1:
        raise RuntimeError(f"Cannot locate downloaded archive for {package} {version}.")
    return matches[0]


# Exact protected files (prefix matching "/etc/modules" would also hit modules-load.d).
_PROTECTED_FILES = ("/etc/modules",)
# Reviewed boot-time module loads that touch no T2 driver, blacklist or initramfs:
#   libvirt-common: "msr" (CPU MSR access for VM CPU feature detection; already loaded here).
#   systemd-zram-generator: "zram" (compressed RAM swap, tasks/resource_policy.py).
_ALLOWED_PATHS = ("/etc/modules-load.d/libvirt-msr.conf", "/usr/lib/modules-load.d/20-zram-generator.conf")


def protected_path(path: str) -> bool:
    path = "/" + path.lstrip("./")
    path = re.sub(r"/+", "/", path)
    if path.startswith(("/lib/", "/lib64/", "/sbin/", "/bin/")):
        path = "/usr" + path
    if path in _ALLOWED_PATHS or path.rstrip("/") in ("/etc/modules-load.d", "/usr/lib/modules-load.d"):
        return False  # a reviewed file, or just the directory entry itself
    return (path in _PROTECTED_FILES or any(path.startswith(p) for p in _PROTECTED_PATHS)
            or bool(_PROTECTED_LIBRARY.match(path)))


def check_archive(deb: Path) -> None:
    """Reject payload paths or maintainer scripts/triggers touching protected state."""
    for line in _run(("/usr/bin/dpkg-deb", "--contents", str(deb))).splitlines():
        path = line.split(None, 5)[-1].split(" -> ")[0]
        if protected_path(path):
            raise RuntimeError(f"{deb.name} installs into protected path {path}; blocked.")
    with tempfile.TemporaryDirectory() as control:
        _run(("/usr/bin/dpkg-deb", "--control", str(deb), control))
        for script in Path(control).iterdir():
            if script.name in ("md5sums", "conffiles", "control", "shlibs", "symbols"):
                continue
            match = _PROTECTED_SCRIPT.search(script.read_bytes())
            if match:
                raise RuntimeError(f"{deb.name} {script.name} references {match[0].decode()}; blocked.")


def install_packages(request: PackageRequest, *, prevent_service_start: bool = False,
                     preview_only: bool = False) -> None:
    """Preview now; schedule a sudo helper only if something is missing."""
    from manage.package_policy import verify_effective_policy
    from manage.package_transaction import inspect_service_policy
    from manage.preflight import validate_local_context
    from pyinfra.operations import server

    validate_local_context()
    validate_request(request)
    request = _with_pending(request)
    verify_effective_policy(preview=True)
    plan = inspect_plan(request)
    if prevent_service_start:
        inspect_service_policy()
    if not (plan.installs or plan.removals) or preview_only:
        return
    project = Path(__file__).resolve().parents[1]
    command = ("cd " + shlex.quote(str(project)) + " && /usr/bin/python3 -m manage.packages --apply "
               + ("--prevent-service-start " if prevent_service_start else "")
               + "".join(f"--replace {shlex.quote(p)} " for p in request.replaces) + shlex.join(request.packages))
    shown = ", ".join(p for p, _ in plan.installs[:6]) + (" ..." if len(plan.installs) > 6 else "")
    if plan.removals:
        shown += f"; replacing {', '.join(plan.removals)}"
    server.shell(name=f"apt install {len(plan.installs)} package(s): {shown}", commands=command, _sudo=True)


def schedule_batch(name: str, *, packages=(), debs=(), source_lists=(), preseed: str = "",
                   cleanup: bool = True) -> None:
    """One guarded transaction for many vendor items (instead of one apt run per app).

    debs: (package, version, url, sha256) to stage in LOCAL_DEBS (downloaded in parallel,
    sha256-checked); source_lists: /etc/apt/sources.list.d/<x>.list names refreshed together
    in one `apt-get update`; packages: archive/repo package names. dpkg then runs once, so
    its triggers (man-db, desktop/MIME/icon caches, ldconfig) run once too.
    """
    import shlex
    from pyinfra.operations import server

    if not (packages or debs):
        return
    project = Path(__file__).resolve().parents[1]
    staged = [f"{LOCAL_DEBS}/{package}_{version}.deb" for package, version, _url, _sha in debs]
    script = ["set -eu", f"install -d -m 755 {LOCAL_DEBS}"]
    if debs:
        script.append("pids=''")
        for (package, version, url, sha), deb in zip(debs, staged):
            script.append(f"( echo '{sha}  {deb}' | sha256sum -c --status - 2>/dev/null || "
                          f"{{ curl -fsSL --proto '=https' --tlsv1.2 -o {deb}.part {shlex.quote(url)} && "
                          f"mv -f {deb}.part {deb} && echo '{sha}  {deb}' | sha256sum -c --quiet -; }} ) & pids=\"$pids $!\"")
        script.append('for p in $pids; do wait "$p"; done')
    if source_lists:
        script += ['parts=$(mktemp -d); trap \'rm -rf "$parts"\' EXIT']
        script += [f"ln -s /etc/apt/sources.list.d/{l}.list \"$parts/\"" for l in source_lists]
        script.append('apt-get update -o Dir::Etc::sourcelist=/dev/null -o Dir::Etc::sourceparts="$parts" '
                      '-o APT::Get::List-Cleanup=0')
    if preseed:
        script.append(preseed)
    script.append(f"cd {shlex.quote(str(project))} && /usr/bin/python3 -m manage.packages --apply "
                  + " ".join(shlex.quote(x) for x in (*packages, *staged)))
    if cleanup and staged:
        script.append("rm -f " + " ".join(staged))
    shown = [p for p in packages] + [d[0] for d in debs]
    server.shell(name=f"{name}: one guarded install of {len(shown)} ({', '.join(shown[:5])}{' ...' if len(shown) > 5 else ''})",
                 commands=["\n".join(script)], _shell_executable="bash", _sudo=True)


def _apply_install(request: PackageRequest, *, prevent_service_start: bool = False) -> None:
    """Root side: re-check policy and plan, inspect archives, then install."""
    if os.geteuid() != 0:
        raise RuntimeError("The package apply helper must run as root (scheduled via sudo).")
    from manage.package_policy import verify_effective_policy
    from manage.package_transaction import package_transaction

    validate_request(request)
    with package_transaction(prevent_service_start=prevent_service_start):
        verify_effective_policy()
        plan = inspect_plan(request)
        if not (plan.installs or plan.removals):
            return
        argv = _apt_args(request)
        if argv is None:
            return   # installed meanwhile
        subprocess.run((argv[0], "--download-only", "--yes", *argv[1:]), env=_ENV, check=True)
        from concurrent.futures import ThreadPoolExecutor
        archives = [_local_deb(package, version, request) or _deb_path(package, version)
                    for package, version in plan.installs]
        with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as pool:
            list(pool.map(check_archive, archives))  # first failure raises here
        subprocess.run((argv[0], "--yes", *argv[1:]), env=_ENV, check=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply a guarded apt install (root)")
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("--prevent-service-start", action="store_true")
    parser.add_argument("--replace", action="append", default=[])
    parser.add_argument("packages", nargs="+")
    arguments = parser.parse_args()
    _apply_install(PackageRequest(tuple(arguments.packages), replaces=tuple(arguments.replace)),
                   prevent_service_start=arguments.prevent_service_start)
