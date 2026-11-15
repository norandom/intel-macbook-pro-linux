# Requirements Document

## Project Description (Input)
The owner of this T2 Linux Mac workstation wants repeatable local system
management for their Ubuntu KDE environment, maintained in this repository
through a Kiro spec-driven workflow.

The repository currently has a bootstrap script, a uv-managed project-local
`.venv`, `pyproject.toml`, and `uv.lock` pinning pyinfra 3.10.0. uv is installed.
The local Node deploy installs nvm 0.41.0 and Node 26.13.1 (pinned in `.nvmrc`),
including npm/npx 11.20.0, and initializes nvm in Bash. This deployment has been
applied and a second run reported no changes. The separate CLI-tool deploy
exists, but installation of btop, Neovim, and its other apt packages has not
been completed because sudo authentication is required.

The intended change is to establish a documented, repeatable foundation for
local management using uv for the Python environment, pyinfra for provisioning,
and nvm for per-user Node.js/npm version management. Node/npm must use nvm,
not system packages. npm global packages belong to the selected nvm-managed
Node version; a custom npm prefix must not be introduced. The foundation should
support the user's forthcoming specification workflow and additional system
management content without assuming a particular npm workflow package.

The source reference is https://github.com/norandom/hyperland-forky-worker-vm.
Selected desktop-independent tooling is intended for porting, including btop
and Neovim. The source's desktop-removal behavior is excluded. The user subsequently
expanded the desired scope to include an optional GPU-backed Hyprland desktop
alongside KDE, selectable through the existing login/session chooser while
preserving its settings and default session, reusable source widgets and
themes, and hypr-rdp. See
`port-intake.md` for the expanded scope, exact turbo controls, and preliminary
laptop compatibility assessment. The foundation remains responsible for uv,
pyinfra, and nvm; the expanded port should be decomposed before formal specs.

This initialization records the agreed baseline and existing implementation,
not approved requirements or a claim that the broader port is complete.
The user will provide substantial additional content before requirements,
design, and implementation tasks are developed.

## Additional user constraint: package policy

Strict rule: no Snap/snapd or Flatpak, including transitive installation and
fallbacks. Preserve the existing snapd apt block and specify reproducible
prevention of prohibited package installation. The observed snapd pin and
project-wide policy are recorded in `../../steering/package-policy.md`.

## Introduction

Provide repeatable local management of the owner's Ubuntu KDE T2 Mac using
the agreed uv/pyinfra foundation and nvm-managed Node/npm. The project-wide
package policy prohibits Snap/snapd and Flatpak.

## Boundary Context

- **In scope:** environment bootstrap, local deployment workflow, Node version
  selection, permitted package installation, and preservation of host state.
- **Out of scope:** GPU power policy, memory/turbo tuning, desktop/widget/theme
  integration, container configuration, and RDP implementation. Their requested
  scope remains in `port-intake.md` for subsequent specifications.
- **Adjacent expectations:** laptop-gpu-policy defines graphics behavior;
  subsequent ports must use the foundation's deployment and package policy.

## Requirements

### Requirement 1: Reproducible management environment
**Objective:** As the laptop owner, I want an isolated management environment,
so that provisioning has reproducible dependencies.

#### Acceptance Criteria
1. When the owner bootstraps the repository, the management workflow shall create a project-local Python environment from the committed dependency lock.
2. If the dependency lock is inconsistent with the project declaration, the management workflow shall report the inconsistency rather than silently change the lock.
3. The management workflow shall keep its Python dependencies separate from the operating system's Python packages.

### Requirement 2: Local deployment and privilege separation
**Objective:** As the laptop owner, I want reviewable local changes, so that I can manage the workstation deliberately.

#### Acceptance Criteria
1. When the owner requests a deployment preview, the management workflow shall report planned changes without applying managed configuration changes.
2. When applying user configuration, the management workflow shall operate as the desktop user.
3. When a system change requires elevated privileges, the management workflow shall request authentication through the local terminal.
4. If authentication or a required operation fails, the management workflow shall report the failure without claiming successful completion.
5. When a deployment is repeated against an already matching host, the management workflow shall leave matching managed configuration unchanged.

### Requirement 3: Per-user Node toolchain
**Objective:** As the laptop owner, I want version-managed Node/npm, so that development tools do not depend on distro Node packages.

#### Acceptance Criteria
1. When the owner provisions the Node toolchain, the management workflow shall install the repository-selected Node version for that user through the agreed version manager.
2. The management workflow shall provide npm and npx with the selected Node version.
3. When the owner opens an interactive Bash terminal, the shell shall make the selected default Node version available.
4. When the owner installs a global npm package, the toolchain shall use the active user's version-managed Node installation without requiring sudo.
5. The management workflow shall preserve existing shell customizations while adding toolchain initialization.
6. The management workflow shall avoid setting a custom npm global prefix that conflicts with the Node version manager.

### Requirement 4: Strict package policy
**Objective:** As the laptop owner, I want prohibited packaging systems excluded, so that every port respects my installation policy.

#### Acceptance Criteria
1. The management workflow shall prohibit installation of Snap/snapd and Flatpak through its package operations, dependencies, and fallback installation paths.
2. The management workflow shall preserve or strengthen the existing apt prohibition on snapd.
3. When evaluating an application installation, the management workflow shall reject packages that delegate installation to Snap or Flatpak.
4. If an application has no permitted installation path, the management workflow shall report that application as unresolved rather than bypass the package policy.
5. The management workflow shall prevent its managed package operations from introducing Flatpak.

### Requirement 5: Preserve the working laptop baseline
**Objective:** As the laptop owner, I want additive provisioning, so that existing desktop and hardware behavior remains usable.

#### Acceptance Criteria
1. The foundation deployment shall preserve KDE, the existing login screen, authentication configuration, and default session.
2. The foundation deployment shall preserve the existing GPU policy and T2 boot configuration.
3. The foundation deployment shall avoid importing source VM desktop-removal, autologin, or software-rendering settings.
4. When reporting deployment results, the management workflow shall distinguish completed operations from pending system changes and validation.
5. The foundation deployment shall preserve the T2 hardware support stack, including kernel/initramfs modules, firmware, touch bar, speakers/microphone, camera, keyboard/trackpad, Wi-Fi/Bluetooth and suspend/resume prerequisites.
6. The foundation deployment shall leave cryptsetup/LUKS, LVM, fstab, swap/resume, installed kernels/modules/headers, bootloader and initramfs/mkinitcpio configuration and artifacts unchanged, including avoiding indirect installer or package-trigger changes.
