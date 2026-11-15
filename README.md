# T2 Mac KDE local management

uv-managed `.venv` with pinned pyinfra dependencies for this Ubuntu 26.04
workstation. Run everything as your desktop user. Only system operations use sudo.

```sh
sh bootstrap.sh

# Preview and install Node.js/npm first.
.venv/bin/pyinfra @local tasks/node.py --dry
.venv/bin/pyinfra @local tasks/node.py

# Preview reviewed native CLI packages, then apply from your terminal.
.venv/bin/pyinfra @local deploy.py --dry
.venv/bin/pyinfra @local deploy.py --same-sudo-password
```

Node/npm are installed per-user with [nvm](https://github.com/nvm-sh/nvm),
with the Node release pinned in `.nvmrc`. This step needs no sudo.
New Bash terminals load nvm automatically. In an existing terminal run:

```sh
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use
node --version
npm --version
```

Changed Bash configuration is backed up beside `.bashrc`.
Optional undo of the managed Bash initialization, preserving nvm data:

```sh
.venv/bin/pyinfra @local tasks/node_restore.py --dry
.venv/bin/pyinfra @local tasks/node_restore.py
```

npm globals belong to the active nvm Node version; use `npm install -g <package>`
without sudo. Do not set npm's `prefix`: it conflicts with nvm.
`npx` comes with Node/npm. CLI system packages still use apt; for those,
`--same-sudo-password` prompts once upfront; `--use-sudo-password` also works
(`manage/preflight.py` teaches pyinfra 3.10 the sudo-rs 0.2 diagnostic).
No spec workflow package has been selected yet.

`uv sync --locked` creates `.venv`; activation is optional (`. .venv/bin/activate`).
The bootstrap installs uv 0.13.8 if uv is missing; an existing uv is preserved.
Run pyinfra directly from `.venv/bin`, or activate the venv and use `pyinfra`.
uv's lock options belong to environment setup, not the pyinfra commands.
System packages follow the configured Ubuntu repositories and are installed if
missing, without a full system upgrade or added third-party repositories.

## Source port and specifications

The implemented baseline includes uv/pyinfra, nvm-managed Node/npm, local-only
preflight, package-plan validation and effective Snap/Flatpak policy checks.
CLI deployment uses the guarded API and an exact reviewed Ubuntu package
manifest. The current plan adds 36 packages, including btop and Neovim, with
zero upgrades or removals. Changed package versions or executable host state
block installation until reviewed again. An already satisfied request remains
a read-only no-op. See the [package review](docs/package-reviews/cli.md).
CLI application requires terminal sudo authentication. The broader desktop port
has not been installed yet.
Completed spec documents are not installed features.

The [source port plan](docs/source-port-plan.md) inventories the actual features
of [hyperland-forky-worker-vm](https://github.com/norandom/hyperland-forky-worker-vm).
The [Kiro roadmap](.kiro/steering/roadmap.md) maps them to resource policy,
containers, fonts, applications, shell/user tools, coordinated themes, the
Hyprland desktop backport and upstream-packaged RDP.

Use Ubuntu's packaged Hyprland with backported configuration/decorations;
use the upstream maintainer's GitHub release for hypr-rdp. KDE stays installed
and dormant as a fallback, with the existing login manager/configuration.
German Mac input preserves the source Super mapping and requires Option+L=@.

Strict rules: no Snap/snapd or Flatpak; preserve the T2 hardware/audio stack.
Do not alter cryptsetup/LUKS/LVM, fstab/swap/resume, kernels/modules/headers,
bootloader or initramfs/mkinitcpio configuration/artifacts, including indirect
package hooks. See [protected system policy](.kiro/steering/protected-system-boundary.md).
These deploy files are intended for `@local` only.
