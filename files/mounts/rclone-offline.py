#!/usr/bin/env python3
"""Managed by t2-mac-kde (tasks/mounts.py). Keep chosen folders of an rclone VFS mount fully in the local cache (offline use).

    rclone-offline.py MOUNTPOINT REMOTE_NAME CACHE_DIR FOLDER [FOLDER...]   loop (from t2-mount)
    rclone-offline.py --once MOUNTPOINT REMOTE_NAME CACHE_DIR FOLDER...    one pass, then exit

rclone has no "pin": a file is offline when the VFS cache holds all of it. Each pass, for every
file under the folders (paths relative to the mount root):
  - not fully cached (new, changed remotely, evicted) -> read through the mount = download
  - fully cached -> only opened and closed: marks it recently used, so the cache keeps it
    (eviction drops the least recently used files first, and after --vfs-cache-max-age)
Runs every INTERVAL while online and the mount is up; ends when the mount goes away.
Log: next to the mount log, <CACHE_DIR>/<REMOTE_NAME>-offline.log
"""
import glob
import json
import os
import subprocess
import sys
import time

INTERVAL = 30 * 60      # seconds between passes
CHUNK = 4 << 20


def log(cache_dir, name, msg):
    with open(os.path.join(cache_dir, f"{name}-offline.log"), "a") as f:
        f.write(time.strftime("%Y/%m/%d %H:%M:%S ") + msg + "\n")


def meta_roots(cache_dir, name):
    """The live vfsMeta/<name> or vfsMeta/<name>{hash} (the hash comes from the backend flags).

    Changing the mount flags makes rclone start a new {hash} folder and abandon the old one, so
    only the most recently written folder counts (an old one would report stale coverage).
    """
    base = os.path.join(cache_dir, "vfsMeta")
    roots = [p for p in glob.glob(os.path.join(glob.escape(base), glob.escape(name) + "*"))
             if os.path.basename(p) == name or os.path.basename(p).startswith(name + "{")]
    return sorted(roots, key=os.path.getmtime)[-1:]


def fully_cached(roots, rel, size):
    if size == 0:           # rclone keeps no cache entry for empty files; nothing to download
        return True
    for root in roots:
        try:
            with open(os.path.join(root, rel)) as f:
                info = json.load(f)
        except (OSError, ValueError):
            continue
        if info.get("Size") != size:
            continue
        covered = sum(r["Size"] for r in info.get("Rs") or [])
        return size == 0 or covered >= size
    return False


def online():
    r = subprocess.run(["nm-online", "-q", "-x", "-t", "0"], capture_output=True)
    return r.returncode == 0 if r.returncode in (0, 1) else True


def one_pass(mnt, name, cache_dir, folders):
    roots = meta_roots(cache_dir, name)
    fetched = kept = failed = total = 0
    for folder in folders:
        top = os.path.join(mnt, folder.strip("/"))
        if not os.path.isdir(top):
            log(cache_dir, name, f"not a folder on {name}: {folder}")
            continue
        for d, _, files in os.walk(top):
            for fn in files:
                path = os.path.join(d, fn)
                rel = os.path.relpath(path, mnt)
                try:
                    size = os.stat(path).st_size
                    total += size
                    cached = fully_cached(roots, rel, size)
                    with open(path, "rb") as f:
                        if not cached:
                            while f.read(CHUNK):
                                pass
                    fetched += not cached
                    kept += cached
                except OSError as e:
                    failed += 1
                    log(cache_dir, name, f"{rel}: {e}")
                if not os.path.ismount(mnt):
                    return False
    log(cache_dir, name, f"pass done: {fetched} downloaded, {kept} already offline, {failed} failed, "
                         f"{total / 2**30:.1f} GiB in offline folders")
    return True


def main():
    args = sys.argv[1:]
    once = args[:1] == ["--once"]
    args = args[once:]
    if len(args) < 4:
        sys.exit(__doc__)
    mnt, name, cache_dir, folders = args[0], args[1], args[2], args[3:]
    for _ in range(60):     # the mount script returns right after the mount is up
        if os.path.ismount(mnt):
            break
        time.sleep(5)
    while os.path.ismount(mnt):
        if online() and not one_pass(mnt, name, cache_dir, folders):
            break
        if once:
            break
        for _ in range(INTERVAL // 10):
            time.sleep(10)
            if not os.path.ismount(mnt):
                break
    if not os.path.ismount(mnt):
        log(cache_dir, name, "mount gone, offline keeper stopped")


if __name__ == "__main__":
    main()
