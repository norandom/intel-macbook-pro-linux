# Research & Design Decisions: Rootless Containers

## Summary
- Feature: rootless-containers, P07 plus exclusive ownership of source podman-tui.
- Discovery scope: complex integration; source-led full discovery with local read-only package inspection and primary official documentation.
- Source revision: `a1c09ec3f02a98b7c6a4641f907108a2ad080993`.
- Findings: actual host is Ubuntu 26.04.1 resolute amd64; native Podman/Compose candidates exist; API socket and Compose are distinct contracts; source scheduling/registry choices require explicit dispositions.
- Specification research is not installation/runtime validation. No containers, downloads, package installations, systemd changes or identity edits were executed.

## Research Log

### Context and consulted workflows
Read AGENTS.md, feature brief, roadmap/package-policy steering, docs/source-port-plan.md, and foundation design. Read kiro-spec-init/requirements/design/tasks and their templates plus EARS/review gates, full discovery, design principles/synthesis and task parallel-analysis rules. Core product.md/tech.md/structure.md files are absent; no substitute policies were invented. kiro-verify-completion supplies the final evidence scope check.

### Actual pinned source
Inspected `/tmp/t2-source-audit/tasks/containers.py`, relevant defaults in `group_data/all.py`, and the release-tools installer in `tasks/apps.py`.

| Source behavior | Local disposition |
| --- | --- |
| Ten native package names including podman-docker, uidmap, passt, netavark/aardvark | Retain reviewed Ubuntu equivalents; explicitly satisfy no-recommends prerequisites |
| `/etc/containers/nodocker` | Create only on compatible clean setup; preserve existing marker |
| docker.io search, permissive short names | Retain source behavior only without policy conflicts; inspect effective user/admin overrides |
| compose_providers podman-compose and warning suppression | Retain with absolute provider path; parse/check installed version |
| docker-compose link | Create only when absent/owned; never replace existing tool |
| Linger enabled | Retain and record prior state; no promise of arbitrary workload auto-restart |
| CPUWeight 200 on user-manager user.slice | Reject automatic import; report current effective policy; optional explicit adoption requires proven placement/controller |
| Socket enabled only when not already enabled | Repair enabled-but-inactive omission by checking enabled and active independently |
| podman-tui v2.0.0 ZIP in global apps release loop | This feature exclusively owns dedicated verified artifact installer |

### Ubuntu/native availability
Read `/etc/os-release`: Ubuntu 26.04.1 LTS, resolute. Read-only `apt-cache policy` (exit 0) showed candidates and no installed versions for podman 5.7.0+ds2-3build1, podman-docker same, podman-compose 1.5.0-2, crun 1.21-1ubuntu3, passt 0.0~git20260120.386b5f5-1, uidmap 1:4.17.4-2ubuntu3, netavark 1.16.1-3.1, aardvark-dns 1.16.0-3, catatonit 0.2.1-2build1, containers-storage 1.61.0+ds1-6, slirp4netns 1.3.3-1 and fuse-overlayfs 1.14-1build2. No podman-tui entry was returned. No apt update or install simulation was run; cache freshness and full maintainer-script/dependency review remain apply prerequisites.

Official [Ubuntu resolute Podman package](https://packages.ubuntu.com/resolute/podman), [podman-docker](https://packages.ubuntu.com/resolute/podman-docker) and [podman-compose](https://packages.ubuntu.com/resolute/podman-compose) pages independently confirm those primary tool versions and native packages. The Podman page lists networking/uidmap/user-session helpers among recommendations, making explicit prerequisite selection necessary with no-recommends. Noble pages were initially inspected, then superseded by resolute evidence; Noble versions are not the target manifest.

### Rootless and lifecycle contracts
[Official Podman rootless documentation](https://docs.podman.io/en/v4.9.3/markdown/podman.1.html) describes subordinate UID/GID mappings, per-user storage, unprivileged networking and local-filesystem constraints. This supports preservation and preflight checks, not hard-coded identity ranges or automatic storage driver migration. Installed 5.7 behavior still needs actual host verification.

[Official Podman API service documentation](https://docs.podman.io/en/latest/markdown/podman-system-service.1.html) establishes user socket activation at the XDG runtime endpoint, separation from the rootful socket and full account-level authority of API access. It documents socket enablement with linger for boot availability. Therefore use the desktop user's Unix socket only and inspect ownership/permissions; keep enabled/active checks separate. Logout/reboot survival is planned validation, not research evidence.

### Compose is a provider integration
[Official Compose wrapper documentation](https://docs.podman.io/en/latest/markdown/podman-compose.1.html) establishes external provider delegation and Docker Compose precedence unless explicitly selected. Source comments claim no socket, but wrapper documentation describes socket environment setup. Design therefore does not promise every Compose path is socket-free; direct podman-compose and wrapper routes require independent acceptance. Older [4.9 documentation](https://docs.podman.io/en/v4.9.3/markdown/podman-compose.1.html) also illustrates version-specific wording, reinforcing installed-version validation.

### Registry and resource policy
[Official registries.conf specification](https://raw.githubusercontent.com/containers/image/main/docs/containers-registries.conf.5.md) explains search registry selection, short-name ambiguity and user-level configuration overrides. Preserve user policy; clean-host source compatibility does not justify silently taking over custom registry configuration.

[Official systemd resource-control reference](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html) defines CPUWeight as relative sibling allocation under cgroup v2: higher values receive more CPU under contention, default kernel weight is 100. Source weight 200 favors its actual sibling branch; it is not inherently a laptop responsiveness optimization. No performance measurement or container cgroup inspection was run. Retain effective scheduling by default and report the decision rather than import a VM assumption.

### Podman-tui artifact route and limits
Source URL and digest are in design.md. [Official podman-tui repository](https://github.com/containers/podman-tui) was inspected for project identity; the raw README path returned 404 and supplied no compatibility evidence. No release archive or checksum was downloaded or independently verified. Native apt-cache has no candidate. Artifact availability, checksum match, ELF dependencies, executable version and API compatibility remain mandatory install/runtime gates.

Foundation PackageRequest has exactly source Literal['ubuntu']; archive installation cannot use it. Foundation design separately permits a reviewed feature design for an upstream artifact with provenance/dependencies/checksum/install behavior. The dedicated route in this spec supplies that contract without modifying foundation. If the route is not accepted in review or the pin fails verification, report podman-tui unresolved, never use an unreviewed fallback.

## Architecture Pattern Evaluation

| Option | Strength | Limitation | Decision |
| --- | --- | --- | --- |
| Copy source module and generic release installer | Small port | Blind Docker takeover, marker-only verification and unsafe extraction assumptions | Reject verbatim copy |
| Native Podman plus bounded dedicated helpers | Matches foundation and preserves runtime data | Requires preflight and explicit acceptance | Adopt |
| Privileged Docker replacement | Familiar daemon API | Outside scope and would conflict with preservation | Reject |
| Invent universal artifact package API | Reusable in theory | Changes upstream ownership and unsupported signature | Reject |

## Design Decisions

### Adopt upstream tools and preserve ownership
Use Ubuntu packages and their shipped units. Dedicated feature files express only source compatibility/lifecycle settings. No new daemon, shell framework, generic package engine or runtime migration subsystem is needed.

### Isolate artifact and restoration contracts
One dedicated checksum-verified TUI route satisfies its source seam without broadening PackageGuard. Receipts back up configuration and lifecycle state; data and identity contracts are never automatically reversed. This simplifies recovery while making retained state explicit.

### Synthesis outcomes
Generalization is limited to shared feature settings and receipts; avoid a cross-project artifact installer. Build only conflict/planning/restoration helpers; adopt Podman, Compose and systemd. Split feature setup from smoke execution so preview and read-only diagnostics remain non-mutating. No dependency from foundation into this feature.

## Risks & Mitigations
- Foundation guard implementation/approval pending: external implementation prerequisite; no duplicate guard here.
- Artifact pin not independently verified: checksum/version/API gates and unresolved status on failure.
- Existing Docker/registry/provider settings unknown: fatal preflight conflict diagnostics with no takeover.
- Namespace/AppArmor/cgroup/storage compatibility untested: diagnose native constraints; no global security bypass.
- Linger affects account lifetime: restore prior state and distinguish API readiness from workload persistence.
- Core steering absent: explicitly recorded limitation; final parent cross-spec review still required.

## Evidence Status
Completed: file/source inspection, current OS/candidate inspection, official documentation review, specification gates. Planned: apt simulation through foundation, artifact verification, subordinate allocation tests, package/config integration, actual containers/Compose/TUI, logout/relogin/reboot and restore acceptance. No runtime pass claimed.
