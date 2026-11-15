# Native CLI package review

Reviewed on 2026-11-15 for the existing Ubuntu 26.04 T2 laptop baseline.
This review covers the exact archive versions and SHA256 values in the CLI
manifest, not future versions or other repository packages. Archives were
downloaded without installing them, their SHA256 values matched native Ubuntu
APT metadata, and every archive control file and payload path was inspected.

The request is curl, ca-certificates, git, jq, unzip, htop, btop, neovim,
ripgrep, fd-find, fzf, gcc, make, bat and tree. Native APT resolves 42 packages:
six already satisfied, 36 newly installed, zero upgrades and zero removals.
No package delegates installation to Snap or Flatpak. No payload or executed
maintainer-script branch changes kernel, initramfs, bootloader, cryptsetup,
LVM, fstab, GPU, T2 drivers, firmware, login or audio configuration.

## Maintainer scripts

Among the 36 new packages, only binutils, gcc and neovim have executable
maintainer scripts. Binutils' preinst moves an obsolete gprofng configuration
only on an old-version upgrade; this is a new installation. GCC registers the
cc/c89/c99 alternatives and cleans a dangling old f77 alternative. Neovim
registers editor/ex/vi/vim/view/vimdiff alternatives and removes obsolete
rview/rvim registrations. Removal scripts remove only those alternatives.
These alternatives do not run a compiler, kernel build or initramfs generator.
The other new packages have no executable maintainer scripts.

Eighteen new library packages contain only an `activate-noawait ldconfig`
trigger declaration. They add no new trigger interests. The installed libc-bin
trigger handler runs ldconfig; its configure-only nsswitch branches do not run.
The current ld.so configuration contains only standard local and multiarch
library directories. This updates the dynamic-linker cache, not boot artifacts.

The already satisfied ca-certificates and git control scripts match the
downloaded archives byte-for-byte; curl, jq, unzip and htop have no executable
control scripts. APT does not reinstall these six packages in this plan.
Ca-certificates would manage its CA store and update hooks on configuration;
the current update-hook directory is empty. Git's scripts concern an obsolete
git Bash-completion conffile and old git cache-directory migration. Neither
package has a boot/storage regeneration path.

## Trigger consumers

Payload paths were matched against every installed file-trigger prefix, rather
than assuming triggers from package names. Only these file consumers match:

- man-db: manual-page files. The triggered branch runs mandb as the man user
  when its auto-update flag is present. AppArmor, tmpfiles and systemd setup
  occur only in its configure branch, which this transaction does not invoke.
- hicolor-icon-theme: htop, btop and Neovim icons. Its triggered branch rebuilds
  only `/usr/share/icons/hicolor` using the installed icon-cache utility.
- desktop-file-utils: htop, btop and Neovim desktop entries. Its triggered
  branch updates only the desktop-file MIME association cache.

No payload matches plymouth, systemd, udev, fontconfig, dbus, CUPS, procps,
shared-mime-info or other registered file-trigger interests. The explicit
ldconfig activation above is the only non-file trigger.

## Effective APT hooks and external inputs

The actual `apt-config dump` install hooks are:

- `dpkg-preconfigure --apt`: extracts Debconf templates/config scripts from
  the selected archives. None of the 36 new packages supplies either; no
  package-supplied preconfiguration program runs. Debconf's installed default
  File/Stack database configuration was inspected.
- PackageKit `StateHasChanged`: the installed D-Bus interface specifies cache
  invalidation. The hook makes that notification; it requests no installation,
  upgrade, removal, refresh transaction or hardware operation.
- update-notifier: touches its dpkg timestamp and updates its MOTD summary.
  The invoked apt-check helper computes update counts using in-memory APT
  dependency state; it does not commit a package transaction.

APT Update hooks for AppStream, command-not-found, update-success timestamps
and Ubuntu Pro services do not run: the guarded installer performs no index
update. No needrestart or kernel regeneration hook is registered here.

The manifest's additional baseline paths bind the inspected external helpers,
their relevant configuration, PackageKit's interface/backend and trigger inputs.
Executable aliases are bound together with their resolved targets. The normal
baseline also binds effective APT configuration, all installed dpkg control
scripts/registrations and package state. A changed baseline requires review
before any actual package installation. A satisfied request is a read-only
no-op; it does not execute the scripts described above.

## Evidence artifacts

The collection workspace is `/tmp/t2-cli-review`: `simulation.txt`,
`metadata.json`, downloaded archives, extracted `control/` files,
`extracted.json` (payload and control hashes), `trigger-matches.json`,
`scripts.txt` and `reviews.json`. The committed machine-readable package
manifest preserves the archive identities and reviewed payload paths; temporary
archives are not repository assets. No live package or hardware changes were
performed during this review.
