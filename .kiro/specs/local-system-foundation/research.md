# Research and Design Decisions

## Summary

- Feature: local-system-foundation.
- Discovery scope: extension; integration-focused discovery of existing scripts.
- Existing uv/pyinfra/nvm implementation is reusable; policy enforcement is missing.
- Package safety requires effective pins, resolution checks and review of native
  packages: a negative pin cannot inspect maintainer scripts.
- No additional Python runtime library or provisioning framework is proposed.

## Research Log

### Existing implementation and skills

Read bootstrap.sh, deploy.py, tasks/node.py, tasks/tools.py, pyproject.toml,
requirements, package steering, and installed pyinfra source. Consulted the
kiro-spec-design skill, light-discovery guidance, design principles, synthesis,
and design-review gate. Core product.md/tech.md/structure.md steering files do
not yet exist; use the approved requirements and package-policy.md as authority.

The existing Node deploy uses nvm shell functions and deferred conditions.
Its default-version check resolves aliases rather than inspecting the configured
alias target. Existing apt calls have no shared prohibition guard. Source VM
settings are not foundation responsibilities.

### External contracts

- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/):
  locked operation checks declaration consistency rather than updating the lock.
- [nvm documentation](https://github.com/nvm-sh/nvm): per-shell initialization,
  per-user version selection and npm prefix compatibility inform Node contracts.
- [Ubuntu apt preferences](https://manpages.ubuntu.com/manpages/resolute/man5/apt_preferences.5.html):
  negative priorities prevent version selection; effective policy must be checked
  because other pins can affect resolution.
- Installed pyinfra 3.10.0 source and CLI help were used to confirm facts,
  operation conditions, dry-run and sudo-password support. A web request for the
  CLI page failed; local installed source remains the version-specific evidence.

These sources validate mechanisms, not successful deployment of the proposed guard.

## Architecture Pattern Evaluation

| Option | Strengths | Limitations | Decision |
| --- | --- | --- | --- |
| Existing pyinfra modules with shared package guard | Small extension, reuse existing facts/results | Requires all package callers to comply | Selected |
| Custom provisioning framework | Centralized orchestration | Duplicates pyinfra with unnecessary maintenance | Rejected |
| Pins alone | Native and simple | Cannot validate script-based transitions or override conflicts | Insufficient alone |

## Design Decisions

### Adopt native lifecycle tools

Keep uv, nvm, apt and pyinfra. Generalize only package policy across installers;
no common abstraction for unrelated desktop/GPU state. This keeps dependency
direction clear and makes subsequent feature deploys consumers of policy.

### Guard managed installation paths

Combine an owned negative-pin file, read-only plan inspection and reviewed native
package manifests. Preserve the user's nosnap.pref. Report existing prohibited
runtimes without automatically deleting applications. Explicitly gate separately
reviewed upstream installers instead of claiming apt simulation inspects scripts.

### Preserve the working host

Foundation write ownership is limited to its environment, Node initialization and
owned apt-policy file. GPU/desktop changes remain in their own specs. Conditional
checks and marked blocks provide repeatability without a second state database.

## Risks and Mitigations

- Apt output/version differences: locale-fixed parsing, fail closed and real
  Ubuntu integration fixtures before apply.
- Package metadata/script drift: revalidate reviewed versions and plans when
  indexes or repositories change; no automatic transition-package fallback.
- User npm conflicts: stop with the exact conflicting setting, preserve credentials.
- Missing core steering: document the limitation; do not invent project policy.
- Partial application: retain nonzero errors and per-operation results; rerun
  matching-state predicates rather than assume transaction-wide rollback.
