"""T2 pack: pinned package versions, their apt pin, .deb backups and release checks.

Owner-approved exception to the protected boundary (2026-11-16, see
.kiro/steering/protected-system-boundary.md): the deploy writes one apt preferences file that
holds the pack's packages at their manifest versions. It never installs, upgrades or removes a
package; moving to a new pack stays an owner-run apt step (docs/t2-pack.md).
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "t2-pack.toml"
SUMS_DIR = ROOT / "packs"
PREF = "/etc/apt/preferences.d/90-t2-pack.pref"
PRIORITY = 990  # beats every repo (500) so nothing newer is picked, never forces a downgrade (>1000)
BACKUP_ROOT = Path(os.path.expanduser("~/.local/share/t2-mac-kde/t2-packs"))

_ID = re.compile(r"^t2-[0-9A-Za-z.+~-]+$")
_PKG = re.compile(r"^[a-z0-9][a-z0-9+.-]+$")
_VER = re.compile(r"^[0-9][0-9A-Za-z.+~:-]*$")


def load(path: Path = MANIFEST) -> dict:
    data = tomllib.loads(Path(path).read_text())
    if not _ID.match(str(data.get("id", ""))):
        raise ValueError(f"{path}: id must look like t2-<kernel version>")
    pkgs = data.get("packages")
    if not isinstance(pkgs, dict) or not pkgs:
        raise ValueError(f"{path}: [packages] is empty")
    for name, ver in pkgs.items():
        if not _PKG.match(name) or not isinstance(ver, str) or not _VER.match(ver):
            raise ValueError(f"{path}: bad entry {name!r} = {ver!r}")
    return data


def pref(pack: dict) -> str:
    out = [f"# Managed by t2-mac-kde (config t2_pack_pin): T2 pack {pack['id']} (t2-pack.toml).",
           "# Holds these packages at the tested versions; newer ones wait for the next pack.",
           "# Remove: t2_pack_pin = false, then run tasks/t2_pack.py.", ""]
    for name, ver in pack["packages"].items():
        out += [f"Package: {name}", f"Pin: version {ver}", f"Pin-Priority: {PRIORITY}", ""]
    return "\n".join(out)


def sums_file(pack: dict) -> Path:
    return SUMS_DIR / f"{pack['id']}.sha256"


def deb_name(name: str, ver: str, arch: str) -> str:
    return f"{name}_{ver.replace(':', '%3a')}_{arch}.deb"


def _run(*argv: str) -> str:
    return subprocess.run(argv, capture_output=True, text=True, check=False).stdout


def installed(name: str) -> str | None:
    out = _run("dpkg-query", "-W", "-f=${db:Status-Status} ${Version}", name).split()
    return out[1] if len(out) == 2 and out[0] == "installed" else None


def available(name: str) -> list[str]:
    """Versions apt knows for a package (from the configured repos), newest first."""
    return [line.split("|")[1].strip() for line in _run("apt-cache", "madison", name).splitlines()
            if line.count("|") >= 2]


def newer(a: str, b: str) -> bool:
    return subprocess.run(["dpkg", "--compare-versions", a, "gt", b]).returncode == 0


def status(pack: dict) -> list[dict]:
    rows = []
    for name, want in pack["packages"].items():
        have = installed(name)
        avail = available(name)
        latest = next((v for v in avail if newer(v, want)), None)
        rows.append({"package": name, "pack": want, "installed": have,
                     "newer": latest, "in_repo": want in avail})
    # A new kernel series appears as a new linux-t2 version; it is reported above.
    return rows


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_sums(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {line.split()[1].lstrip("*"): line.split()[0] for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")}


def backup(pack: dict, dest: Path | None = None, write_sums: bool = False) -> Path:
    """Download the pack's .debs (apt verifies them against the signed repo index), then check
    them against packs/<id>.sha256 when it exists. write_sums=True records it (first backup)."""
    dest = dest or BACKUP_ROOT / pack["id"]
    dest.mkdir(parents=True, exist_ok=True)
    have = {p.name for p in dest.glob("*.deb")}
    missing = [f"{n}={v}" for n, v in pack["packages"].items()
               if not any(f.startswith(f"{n}_{v.replace(':', '%3a')}_") for f in have)]
    if missing:
        r = subprocess.run(["apt-get", "download", *missing], cwd=dest, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f"apt-get download failed (version gone from the repos?):\n{r.stderr.strip()}")
    debs = sorted(dest.glob("*.deb"))
    got = {p.name: sha256(p) for p in debs}
    for n, v in pack["packages"].items():
        if not any(k.startswith(f"{n}_{v.replace(':', '%3a')}_") for k in got):
            raise RuntimeError(f"backup lacks {n} {v}")
    lines = "".join(f"{h}  {n}\n" for n, h in sorted(got.items()))
    (dest / "SHA256SUMS").write_text(lines)
    ref = read_sums(sums_file(pack))
    if ref:
        bad = [n for n, h in got.items() if ref.get(n) != h]
        lost = [n for n in ref if n not in got]
        if bad or lost:
            raise RuntimeError(f"backup differs from {sums_file(pack).name}: changed {bad}, missing {lost}")
    elif write_sums:
        SUMS_DIR.mkdir(exist_ok=True)
        sums_file(pack).write_text(f"# T2 pack {pack['id']}: sha256 of the backed-up .debs (tools/t2-pack backup)\n"
                                   + lines)
    return dest
