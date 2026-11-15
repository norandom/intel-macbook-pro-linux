"""Fail-closed, read-only native Ubuntu package planning.

Admission is a code-reviewed manifest, never inferred from package names or a
keyword scan. Each entry binds the reviewed .deb (including control scripts,
triggers and payload) to its SHA256 and the reviewed local dpkg/apt state. Review
must trace installed trigger consumers and effective apt hooks, including their
external inputs in ``additional_state_paths``. A review asserts no Snap/Flatpak
delegation and no protected-system effects. Index/package or local state changes
require new review. There are deliberately no approved production entries yet:
the current CLI manifest is reviewed in the integration task, not here.
"""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import stat
import subprocess
from typing import Literal


@dataclass(frozen=True)
class PackageRequest:
    packages: tuple[str, ...]
    source: Literal["ubuntu"]


@dataclass(frozen=True)
class PackagePlan:
    installs: tuple[tuple[str, str], ...]
    removals: tuple[str, ...]


@dataclass(frozen=True)
class _PackageReview:
    package: str
    version: str
    architecture: str
    deb_sha256: str
    baseline_sha256: str
    evidence: str
    native: bool
    scripts_reviewed: bool
    triggers_reviewed: bool
    apt_hooks_reviewed: bool
    paths: tuple[str, ...]
    additional_state_paths: tuple[str, ...] = ()


_REVIEWS: tuple[_PackageReview, ...] = ()
_SELECTION = re.compile(r"([a-z0-9][a-z0-9+.-]+)(?::([a-z0-9][a-z0-9-]*))?(?:=([0-9][a-zA-Z0-9.+:~\-]*))?\Z")
_FORBIDDEN = {"snap", "snapd", "flatpak"}
_PROTECTED = re.compile(r"(?:linux(?:-|$)|grub|shim|efibootmgr|bootctl|ukify|kernel-install|initramfs|mkinit|dracut|cryptsetup|lvm|libcryptsetup|libdevmapper|liblvm|dmsetup|thin-provisioning|dkms|kmod|systemd(?!-zram-generator$)|udev|firmware|apple-|t2-|pipewire|wireplumber|alsa-)")
_PROTECTED_PATHS = ("/boot", "/lib/modules", "/usr/lib/modules", "/usr/src", "/etc/fstab",
                    "/etc/crypttab", "/etc/cryptsetup", "/etc/lvm", "/etc/initramfs-tools",
                    "/usr/share/initramfs-tools", "/etc/mkinit", "/etc/dracut",
                    "/usr/lib/dracut", "/etc/default/grub", "/etc/grub", "/etc/kernel",
                    "/usr/lib/kernel", "/etc/modules", "/etc/modprobe", "/etc/firmware",
                    "/lib/firmware", "/usr/lib/firmware", "/etc/swap", "/etc/resume",
                    "/usr/lib/cryptsetup", "/usr/share/cryptsetup", "/usr/sbin/update-initramfs",
                    "/usr/sbin/mkinit", "/usr/sbin/dracut", "/usr/sbin/update-grub",
                    "/usr/sbin/grub-", "/usr/sbin/cryptsetup", "/usr/sbin/lvm",
                    "/usr/lib/initramfs-tools", "/usr/lib/initcpio", "/usr/share/initcpio",
                    "/usr/lib/mkinit", "/usr/share/mkinit", "/etc/initcpio",
                    "/usr/lib/grub", "/usr/share/grub", "/etc/bootloader",
                    "/usr/lib/systemd/boot", "/usr/lib/systemd/ukify",
                    "/usr/lib/systemd/system-generators/systemd-cryptsetup-generator",
                    "/usr/lib/systemd/system-generators/systemd-fstab-generator",
                    "/usr/lib/systemd/system-generators/systemd-gpt-auto-generator",
                    "/usr/lib/systemd/system-generators/systemd-hibernate-resume-generator",
                    "/usr/bin/bootctl", "/usr/sbin/bootctl", "/usr/bin/kernel-install",
                    "/usr/bin/ukify", "/usr/bin/mkinit", "/usr/bin/dracut",
                    "/usr/lib/shim", "/usr/share/shim", "/usr/bin/efibootmgr",
                    "/usr/sbin/efibootmgr", "/usr/bin/grub-", "/usr/bin/update-grub",
                    "/usr/bin/update-initramfs")
_PROTECTED_LIBRARY_PATH = re.compile(
    r"^/(?:usr/)?(?:local/)?lib(?:32|64|x32)?/(?:[^/]+/)*(?:libcryptsetup|libdevmapper|liblvm)[^/]*$"
)
_MAX_PACKAGES = 128
_MAX_OUTPUT = 4 * 1024 * 1024


def _selection(value: str) -> tuple[str, str | None, str | None]:
    match = _SELECTION.fullmatch(value) if isinstance(value, str) else None
    if not match or len(value) > 256 or match[2] in ("any", "native"):
        raise RuntimeError("Invalid package selection: use a native name[:architecture][=exact-version].")
    name, architecture, version = match.groups()
    if (name in _FORBIDDEN or name.startswith(("snapd-", "flatpak-", "libflatpak", "libsnapd"))
            or name.endswith(("-plugin-snap", "-plugin-flatpak", "-backend-snap", "-backend-flatpak"))
            or _PROTECTED.match(name)):
        raise RuntimeError(f"Prohibited or protected package: {name}; installation unresolved.")
    return name, architecture, version


def _canonical_single_root(path: str) -> bool:
    """Require literal canonical Linux paths; POSIX preserves ambiguous // roots."""
    return (isinstance(path, str) and path.startswith("/") and not path.startswith("//")
            and "\x00" not in path and str(PurePosixPath(path)) == path
            and ".." not in PurePosixPath(path).parts)


def _check_review(review: _PackageReview) -> None:
    if (not review.evidence.strip() or not all((review.native, review.scripts_reviewed,
            review.triggers_reviewed, review.apt_hooks_reviewed))
            or not re.fullmatch(r"[a-f0-9]{64}", review.deb_sha256)
            or not re.fullmatch(r"[a-f0-9]{64}", review.baseline_sha256)
            or not review.paths):
        raise RuntimeError("Native package/script/trigger/hook review evidence is incomplete; installation unresolved.")
    if any(not _canonical_single_root(path) for path in review.additional_state_paths):
        raise RuntimeError("Review baseline paths must be canonical single-root absolute paths.")
    for path in review.paths:
        if not _canonical_single_root(path):
            raise RuntimeError("Reviewed payload uses an unrecognized noncanonical path.")
        # usrmerge aliases address the same protected executables and libraries.
        canonical = "/usr" + path if path.startswith(("/sbin/", "/bin/", "/lib/")) else path
        if (any(canonical.startswith(prefix) for prefix in _PROTECTED_PATHS)
                or _PROTECTED_LIBRARY_PATH.fullmatch(path)):
            raise RuntimeError("Reviewed payload affects a protected or unrecognized path; installation unresolved.")


def _reviews(name: str, architecture=None, version=None) -> tuple[_PackageReview, ...]:
    matches = tuple(r for r in _REVIEWS if r.package == name
                    and (architecture is None or r.architecture == architecture)
                    and (version is None or r.version == version))
    if not matches:
        raise RuntimeError(f"Unreviewed package/version/architecture: {name}; installation unresolved.")
    for review in matches:
        _check_review(review)
    return matches


def validate_request(request: PackageRequest) -> None:
    """Reject unsafe arguments and anything without explicit native review."""
    if (not isinstance(request, PackageRequest) or request.source != "ubuntu"
            or not isinstance(request.packages, tuple)
            or not 0 < len(request.packages) <= _MAX_PACKAGES):
        raise RuntimeError("A nonempty bounded tuple of reviewed Ubuntu packages is required.")
    names = set()
    for selection in request.packages:
        name, architecture, version = _selection(selection)
        if name in names:
            raise RuntimeError("Duplicate or conflicting package selections are not allowed.")
        names.add(name)
        _reviews(name, architecture, version)


def _baseline_digest(additional_paths: tuple[str, ...] = ()) -> str:
    """Bind review to installed scripts, trigger state, payload lists and apt config.

    Never print file content or the digest. Symlinks, unreadable evidence and
    oversized inventories block admission. Apt preferences are excluded: these
    express resolution policy, not executable hooks, and PackagePolicy owns their
    effective verification. Adding its negative pins does not invalidate review.
    External apt-hook/config dependencies
    must be included by the review; the attestation is a human review contract.
    """
    roots = ("/var/lib/dpkg/status", "/var/lib/dpkg/info", "/var/lib/dpkg/triggers",
             "/var/lib/dpkg/updates", "/etc/apt") + additional_paths
    digest = hashlib.sha256()
    total = count = 0
    try:
        for root in sorted(set(roots)):
            if not _canonical_single_root(root):
                raise RuntimeError("Invalid review baseline path.")
            paths = [Path(root)]
            while paths:
                path = paths.pop()
                if (path in (Path("/etc/apt/preferences"), Path("/etc/apt/preferences.d"))
                        and root not in additional_paths):
                    continue
                info = path.lstat()
                count += 1
                if count > 100000 or stat.S_ISLNK(info.st_mode):
                    raise RuntimeError("Unrecognized or oversized review baseline.")
                digest.update(str(path).encode() + b"\0" + str(info.st_mode).encode() + b"\0")
                if stat.S_ISDIR(info.st_mode):
                    children = sorted(path.iterdir(), reverse=True)
                    if path == Path("/var/lib/dpkg/updates") and children:
                        raise RuntimeError("Pending dpkg updates block package planning.")
                    paths.extend(children)
                elif stat.S_ISREG(info.st_mode):
                    total += info.st_size
                    if total > 512 * 1024 * 1024:
                        raise RuntimeError("Oversized review baseline.")
                    data = path.read_bytes()
                    if (path == Path("/var/lib/dpkg/triggers/Unincorp") and data.strip()
                            or path == Path("/var/lib/dpkg/status") and
                            re.search(rb"^Status: .*triggers-(?:pending|awaited)$", data, re.M)):
                        raise RuntimeError("Pending dpkg triggers block package planning.")
                    digest.update(len(data).to_bytes(8, "big") + data)
                else:
                    raise RuntimeError("Unrecognized review baseline file type.")
    except OSError as error:
        raise RuntimeError("Cannot read package/script/trigger/apt review baseline; installation unresolved.") from error
    return digest.hexdigest()


def _run(argv: tuple[str, ...]) -> str:
    # In particular, inherited APT_CONFIG, HOME, locale and shell overrides must
    # not redirect apt away from the state whose evidence was reviewed.
    try:
        result = subprocess.run(argv, env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C", "LANG": "C"},
                                capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError, UnicodeError) as error:
        raise RuntimeError("Native apt inspection failed; installation unresolved.") from error
    if result.returncode or result.stderr.strip() or len(result.stdout) > _MAX_OUTPUT:
        raise RuntimeError("Native apt inspection failed or produced diagnostics; installation unresolved.")
    return result.stdout


def _parse_simulation(output: str):
    installs, configurations, satisfied = {}, {}, {}
    manual_markers = set()
    summary = None
    list_header = False
    upgraded = newly = 0
    headers = {"The following NEW packages will be installed:", "The following packages will be upgraded:",
               "The following additional packages will be installed:", "Suggested packages:", "Recommended packages:"}
    boilerplate = {"NOTE: This is only a simulation!", "      apt-get needs root privileges for real execution.",
                   "      Keep also in mind that locking is deactivated,",
                   "      so don't depend on the relevance to the real current situation!",
                   "Reading package lists...", "Building dependency tree...", "Reading state information...",
                   "Solving dependencies..."}
    for line in output.splitlines():
        if not line or line in boilerplate:
            continue
        if line in headers:
            list_header = True
            continue
        if list_header and re.fullmatch(r"  [a-zA-Z0-9+.:()<>~ =|\-]+", line):
            continue
        list_header = False
        match = re.fullmatch(r"(\d+) upgraded, (\d+) newly installed, (\d+) to remove and (\d+) not upgraded\.", line)
        if match:
            if summary is not None or int(match[3]):
                raise RuntimeError("Package removals or duplicate simulation summary block the plan.")
            summary = tuple(map(int, match.groups()))
            continue
        match = re.fullmatch(r"(Inst|Conf) (\S+)(?: \[([^\]]+)\])? \((\S+) (Ubuntu:[^\s]+) \[([a-z0-9-]+)\]\)", line)
        if match:
            kind, package, previous, version, origin, architecture = match.groups()
            name, qualifier, _ = _selection(package)
            if qualifier and qualifier != architecture:
                raise RuntimeError("Architecture disagreement in apt simulation.")
            target = installs if kind == "Inst" else configurations
            if name in target or len(target) >= _MAX_PACKAGES:
                raise RuntimeError("Duplicate or oversized apt plan.")
            target[name] = (package, version, architecture)
            if kind == "Inst":
                upgraded += previous is not None
                newly += previous is None
            continue
        match = re.fullmatch(r"(\S+) is already the newest version \((\S+)\)\.", line)
        if match:
            name, architecture, _ = _selection(match[1])
            if name in satisfied:
                raise RuntimeError("Duplicate satisfied package in apt output.")
            satisfied[name] = (match[1], match[2], architecture)
            continue
        match = re.fullmatch(r"(\S+) set to manually installed\.", line)
        if match:
            name, _, _ = _selection(match[1])
            if (name not in satisfied or satisfied[name][0] != match[1]
                    or name in manual_markers):
                raise RuntimeError("Unexpected or duplicate manual package marker in apt output.")
            manual_markers.add(name)
            continue
        raise RuntimeError("Unrecognized apt simulation output; installation unresolved.")
    if summary is None or summary[:2] != (upgraded, newly) or configurations != installs:
        raise RuntimeError("Incomplete or inconsistent apt simulation; installation unresolved.")
    return installs, satisfied


def _metadata(package: str, version: str, architecture: str | None) -> _PackageReview:
    name, qualifier, _ = _selection(package)
    _reviews(name, architecture or qualifier, version)
    selected = package if qualifier or architecture is None else f"{package}:{architecture}"
    records = _run(("/usr/bin/apt-cache", "show", f"{selected}={version}")).strip().split("\n\n")
    admitted = []
    for record in records:
        fields = {}
        for line in record.splitlines():
            if line.startswith((" ", "\t")):
                continue
            key, separator, value = line.partition(": ")
            if not separator or key in fields:
                raise RuntimeError("Malformed or ambiguous apt package metadata.")
            fields[key] = value
        name, qualifier, _ = _selection(package)
        if (fields.get("Package") != name or fields.get("Version") != version
                or fields.get("Origin") != "Ubuntu" or not fields.get("Architecture")
                or architecture is not None and fields["Architecture"] != architecture
                or qualifier is not None and fields["Architecture"] != qualifier):
            raise RuntimeError("Unknown or inconsistent native Ubuntu source metadata.")
        reviews = _reviews(name, fields["Architecture"], version)
        matches = [r for r in reviews if r.deb_sha256 == fields.get("SHA256")]
        if len(matches) != 1:
            raise RuntimeError("Package content is unreviewed or ambiguous; installation unresolved.")
        admitted.append(matches[0])
    if not admitted or any(review != admitted[0] for review in admitted):
        raise RuntimeError("Ambiguous apt source metadata; installation unresolved.")
    return admitted[0]


def inspect_plan(request: PackageRequest) -> PackagePlan:
    """Simulate the exact validated arguments, retaining only reviewed changes."""
    validate_request(request)
    # Baseline must be reviewed before invoking apt as well as after its reads.
    reviews = tuple(r for r in _REVIEWS)
    additional = tuple(sorted({p for r in reviews for p in r.additional_state_paths}))
    baseline = _baseline_digest(additional)
    requested_reviews = tuple(r for selection in request.packages for r in _reviews(*_selection(selection)))
    if any(r.baseline_sha256 != baseline for r in requested_reviews):
        raise RuntimeError("Package review baseline changed; scripts/triggers/hooks need review.")
    output = _run(("/usr/bin/apt-get", "--simulate", "--no-install-recommends", "--no-remove", "install", *request.packages))
    installs, satisfied = _parse_simulation(output)
    observed = {**satisfied, **installs}
    for selection in request.packages:
        name, architecture, version = _selection(selection)
        if name not in observed:
            raise RuntimeError("Requested package was not resolved by apt; installation unresolved.")
        package, resolved, resolved_arch = observed[name]
        if architecture and resolved_arch is None:
            observed[name] = (package, resolved, architecture)
        if version is not None and version != resolved or architecture and resolved_arch and architecture != resolved_arch:
            raise RuntimeError("Resolved package selection differs from request.")
    for package, version, architecture in observed.values():
        review = _metadata(package, version, architecture)
        if review.baseline_sha256 != baseline:
            raise RuntimeError("Dependency review baseline changed; scripts/triggers/hooks need review.")
    if _baseline_digest(additional) != baseline:
        raise RuntimeError("Package baseline changed during inspection; retry after review.")
    return PackagePlan(tuple((package, version) for package, version, _ in installs.values()), ())


def install_packages(request: PackageRequest, *, prevent_service_start: bool = False) -> None:
    """Preview a guarded request and schedule its revalidation under sudo.

    The package-policy operation must precede this operation in the deploy.
    Preview validates its prospective policy without writing system preferences;
    apply requires the real policy and reruns all package evidence checks.
    Index refreshes are deliberately separate: this function never updates apt
    indexes after review or offers arbitrary apt options.
    """
    if prevent_service_start:
        raise RuntimeError("Guarded service-start suppression is not implemented yet; installation unresolved.")
    from manage.package_policy import verify_effective_policy
    from manage.preflight import validate_local_context
    from pyinfra.operations import server

    validate_local_context()
    validate_request(request)
    verify_effective_policy(preview=True)
    plan = inspect_plan(request)
    if not plan.installs:
        return
    project = Path(__file__).resolve().parents[1]
    command = ("cd " + shlex.quote(str(project))
               + " && /usr/bin/python3 -m manage.packages --apply "
               + shlex.join(request.packages))
    server.shell(name="Install reviewed native Ubuntu packages", commands=command, _sudo=True)


def _apply_install(request: PackageRequest) -> None:
    """Privileged execution boundary; re-read current policy, indexes and state."""
    if os.geteuid() != 0:
        raise RuntimeError("The package apply helper requires root via the scheduled sudo operation.")
    from manage.package_policy import verify_effective_policy

    validate_request(request)
    verify_effective_policy()
    plan = inspect_plan(request)
    if not plan.installs:
        return
    subprocess.run(
        ("/usr/bin/apt-get", "--no-install-recommends", "--no-remove", "--yes", "install", *request.packages),
        env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C", "LANG": "C"},
        check=True,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply a reviewed native Ubuntu package request")
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("packages", nargs="+")
    arguments = parser.parse_args()
    _apply_install(PackageRequest(tuple(arguments.packages), "ubuntu"))
