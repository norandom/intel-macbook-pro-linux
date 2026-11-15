# Implementation Tasks: Rootless Containers

Implemented in `tasks/containers.py` (deploy) + `manage/containers.py` (read-only helpers),
tests in `tests/test_containers.py`. Ported from source `tasks/containers.py` and the
podman-tui entry of source `group_data/all.py` `release_tools`.

Run: `.venv/bin/pyinfra @local tasks/containers.py` (preview with `--dry`).

## Done
- [x] Native packages via guarded `install_packages` (source "ubuntu"): podman, crun, passt, uidmap,
      netavark, aardvark-dns, catatonit, containers-storage, podman-compose, podman-docker
      (recommends listed explicitly because installs use `--no-install-recommends`).
- [x] Existing Docker (docker.io/docker-ce/docker-cli/moby packages, foreign `docker` command,
      DOCKER_HOST/CONTAINER_HOST/PODMAN_COMPOSE_PROVIDER) detected: podman-docker skipped, reported, nothing removed.
- [x] Subordinate IDs: valid existing ranges kept (mc already has 100000:65536); if absent, a
      nonoverlapping 65536 range is appended with `usermod --add-sub{u,g}ids`; undersized range stops.
- [x] `/etc/containers/nodocker` (only if absent).
- [x] Short-name policy `registries.conf.d/60-t2-containers.conf` (docker.io, permissive) unless a
      user `~/.config/containers/registries.conf` or CONTAINERS_REGISTRIES_CONF exists (then reported, preserved).
- [x] `containers.conf.d/60-t2-containers.conf`: compose_providers = /usr/bin/podman-compose, no warning logs.
- [x] `/usr/local/bin/docker-compose -> /usr/bin/podman-compose` only when absent or already ours.
- [x] Linger enabled for the desktop user (skipped if already on).
- [x] User `podman.socket` enabled (socket-activated, user-only API for podman-tui); no root daemon/TCP listener.
- [x] podman-tui: not in the Ubuntu 26.04 archive -> upstream v2.0.0 linux_amd64 zip, sha256
      de1de103...442f pinned, verified before extraction, version-checked, installed to
      `~/.local/opt/podman-tui-2.0.0/`, linked from `~/.local/bin/podman-tui` (foreign file preserved).
- [x] Source CPUWeight=200 for the container slice deliberately NOT applied (laptop responsiveness); reported.
- [x] Unit tests for subid parsing/allocation and Docker conflict detection.

## Deferred / needs live owner check
- [ ] Live apply and acceptance: `podman info` rootless=true, run a container with DNS/outbound + volume,
      `docker`, `docker compose`, `docker-compose`, `podman compose` all use podman-compose; requires owner sudo run.
- [ ] Confirm the Ubuntu podman package does not enable the system (root) `podman.socket`; disable manually if it does.
- [ ] podman-tui connection to the user socket (`podman-tui` lists the test container) — live check.
- [ ] Restoration tooling / state receipts: not implemented (speed policy); managed files are the three
      `/etc/containers` fragments, the docker-compose link and `~/.local/opt/podman-tui-*` — remove by hand.
- [ ] Optional CPU weight adoption: needs observed cgroup placement; owner decision.
- [ ] Logout/reboot lifecycle checks: manual.
