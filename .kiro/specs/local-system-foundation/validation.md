# Foundation implementation validation

- DECISION: GO for owner-run foundation deployment.
- Scope: uv/pyinfra bootstrap, user nvm/Node/npm, native CLI installation and
  shared package-policy guards. This does not claim installation of Hyprland,
  resource tuning, containers, themes or RDP.

## Mechanical evidence

- `.venv/bin/python -m unittest discover -s tests -q`: 95 passed, no skips,
  exit 0. Includes six native Ubuntu namespace integration tests.
- `.venv/bin/python -m compileall -q manage tasks tests`: exit 0.
- `sh -n bootstrap.sh` and `git diff --check`: exit 0.
- `.venv/bin/pyinfra @local deploy.py --dry`: reaches its operation preview;
  36 reviewed package additions, zero upgrades and zero removals.
- Independent task reviews approved 4.1 and 4.2–4.4. Placeholder and secret
  checks found no blocking findings.

## Requirements and integration

| Requirement section | Implementation and evidence |
| --- | --- |
| 1. Reproducible environment | Locked bootstrap; real offline uv success/stale-lock tests and isolated environment checks. |
| 2. Local execution and privileges | Shared local-user preflight; actual desktop-user preview and namespace-root apply; authentication and partial-failure integration checks. |
| 3. User Node toolchain | Pinned nvm/Node, bundled npm/npx checks, exact alias, conflict diagnostics, additive Bash block, backup and scoped restoration. Live Node/npm verified; repeated Node apply made no changes. |
| 4. Strict package policy | Exact 42-archive review, effective negative pins, protected dependency/script/trigger gates, native installation, prohibited-runtime and conflicting-pin failures. |
| 5. Working baseline | Read-only protected mounts, before/after snapshots, unchanged original snapd block, scoped restoration and no package removals. Physical hardware acceptance remains manual. |

Bootstrap, preflight, policy, package guard and user provisioning retain the
design's dependency direction. Feature modules consume the package contract;
foundation imports no desktop, GPU or RDP implementation. The only additional
implementation modules provide one clear responsibility each: npm checks and
recoverable service-start suppression. Review data is committed separately
from the guard. No blocked foundation tasks remain.

## Deployment handoff and limits

The owner performs live deployment. The earlier attempted live system operation
failed authentication before executing any system command; the readable
protected-file and protected-package snapshot remained identical. No successful
CLI installation is claimed. Follow the direct venv pyinfra commands in README.

The isolated Node installation uses existing-toolchain fixtures; actual Node
download behavior is outside those six integration tests. Actual microphone,
camera, touch bar, speakers, Bluetooth and suspend/resume acceptance remains
pending. See `docs/foundation-integration.md` for exact fixture boundaries and
`docs/package-reviews/cli.md` for the native archive and hook review.
