# Source application inventory

Pinned source revision: a1c09ec3f02a98b7c6a4641f907108a2ad080993.
Every literal apt entry in tasks/apps.py is listed. A candidate in local apt
metadata is not a verified permitted installer; maintainer/dependency review
and source-origin checks are still required before install.

| Source apt package | Ownership or disposition |
| --- | --- |
| aria2 | application-suite; native route candidate, review pending |
| atop | application-suite; native route candidate, review pending |
| bat | foundation current CLI install ownership; application-suite observes availability, no duplicate installation |
| c3270 | application-suite; native route candidate, review pending |
| chromium | no Debian-named candidate in inspected Ubuntu indexes; reject Snap transition; native artifact route evaluation pending |
| chromium-driver | no Debian-named candidate in inspected Ubuntu indexes; reject Snap transition; native artifact route evaluation pending |
| cliphist | delegated installation to hyprland-desktop; application-suite observes/reports availability only |
| fd-find | foundation current CLI install ownership; application-suite observes availability, no duplicate installation |
| fonts-crosextra-carlito | deferred LibreOffice backlog; no current install/configuration |
| foot | application-suite owns package; coordinated-themes owns configuration |
| fzf | foundation current CLI install ownership; application-suite observes availability, no duplicate installation |
| gcc | foundation current CLI install ownership; application-suite observes availability, no duplicate installation |
| gdu | application-suite; native route candidate, review pending |
| gh | application-suite; native route candidate, review pending |
| git | foundation current CLI install ownership; application-suite observes availability, no duplicate installation |
| glow | application-suite; native route candidate, review pending |
| golang-go | application-suite; native route candidate, review pending |
| hunspell-de-de | deferred LibreOffice backlog; no current install/configuration |
| hunspell-en-us | deferred LibreOffice backlog; no current install/configuration |
| hyphen-de | deferred LibreOffice backlog; no current install/configuration |
| hyphen-en-us | deferred LibreOffice backlog; no current install/configuration |
| lazygit | application-suite; native route candidate, review pending |
| libreoffice-calc | deferred LibreOffice backlog; no current install/configuration |
| libreoffice-gtk3 | deferred LibreOffice backlog; no current install/configuration |
| libreoffice-l10n-de | deferred LibreOffice backlog; no current install/configuration |
| libreoffice-writer | deferred LibreOffice backlog; no current install/configuration |
| make | foundation current CLI install ownership; application-suite observes availability, no duplicate installation |
| meld | application-suite; native route candidate, review pending |
| multitail | application-suite; native route candidate, review pending |
| mythes-de | deferred LibreOffice backlog; no current install/configuration |
| mythes-en-us | deferred LibreOffice backlog; no current install/configuration |
| nedit | application-suite; native route candidate, review pending |
| neovim | application-suite owns native binary; shell-user-tools owns nvim-simple config |
| nodejs | excluded system package; foundation owns nvm replacement |
| npm | excluded system package; foundation owns nvm replacement |
| posting | application-suite; native route candidate, review pending |
| qpdfview | application-suite; native route candidate, review pending |
| ripgrep | foundation current CLI install ownership; application-suite observes availability, no duplicate installation |
| ristretto | application-suite; native route candidate, review pending |
| rsync | application-suite; native route candidate, review pending |
| rust-coreutils | application-suite; native route candidate, review pending |
| sublime-text | vendor route; inspect existing source, do not pretend Ubuntu-origin guard accepts vendor packages |
| tree | foundation current CLI install ownership; application-suite observes availability, no duplicate installation |
| trippy | application-suite; native route candidate, review pending |
| typora | vendor route; inspect existing source, do not pretend Ubuntu-origin guard accepts vendor packages |
| unzip | foundation current CLI install ownership; application-suite observes availability, no duplicate installation |
| vivaldi-stable | vendor route; inspect existing source, do not pretend Ubuntu-origin guard accepts vendor packages |
| x11-xserver-utils | delegated installation to desktop-fonts for xset; application-suite observes/reports availability only |
| x3270 | application-suite; native route candidate, review pending |
| xfce4-terminal | application-suite owns package; coordinated-themes owns configuration |
| xpdf | application-suite; native route candidate, review pending |

## release_tools

| Source name | Disposition |
| --- | --- |
| podman-tui | rootless-containers owns installer |
| zellij | application-suite; compatible native artifact route or explicit unresolved status required |
| upmd | application-suite; compatible native artifact route or explicit unresolved status required |
| kubectl | application-suite; compatible native artifact route or explicit unresolved status required |
| helm | application-suite; compatible native artifact route or explicit unresolved status required |
| k9s | application-suite; compatible native artifact route or explicit unresolved status required |
| ktop | application-suite; compatible native artifact route or explicit unresolved status required |
| bw | application-suite; compatible native artifact route or explicit unresolved status required |
| rc | application-suite; compatible native artifact route or explicit unresolved status required |
| rclone | application-suite; compatible native artifact route or explicit unresolved status required |

## artcraft_apps

| Source name | Disposition |
| --- | --- |
| pdfcraft | deferred Craft suite backlog; retain source installer references |
| designcraft | deferred Craft suite backlog; retain source installer references |
| gridcraft | deferred Craft suite backlog; retain source installer references |
| lightcraft | deferred Craft suite backlog; retain source installer references |
| wordcraft | deferred Craft suite backlog; retain source installer references |
| deckcraft | deferred Craft suite backlog; retain source installer references |
| cadcraft | deferred Craft suite backlog; retain source installer references |

## client_debs

| Source name | Disposition |
| --- | --- |
| quarto | application-suite; compatible native artifact route or explicit unresolved status required |
| positron | application-suite; compatible native artifact route or explicit unresolved status required |
| code | application-suite; compatible native artifact route or explicit unresolved status required |

## Additional literal artifact applications

Obsidian, Bitwarden desktop and Ghostty are declared by version/checksum in
source tasks/apps.py. They need compatible Ubuntu artifacts; the source's
Ghostty forky .deb is not accepted as an Ubuntu build. No inherited purge logic.

## Evidence

Local `apt-cache policy` was read without installation. The raw results for
source apt names are recorded in package-candidates.txt; sources may change
before implementation and candidate presence is not a successful deploy.

## Base CLI entries

Source tasks/base.py adds sudo, curl, ca-certificates, git, jq, unzip, htop,
btop, dbus-user-session, systemd-zram-generator, earlyoom and qemu-guest-agent.
The existing foundation CLI list owns its overlapping binaries until an explicit
integration migration. desktop handles session prerequisites; resource-policy
owns zram-generator/earlyoom; qemu-guest-agent is excluded on this laptop.
No desktop/display-manager removals are ported.

## Auxiliary source-desktop application prerequisites

These binaries came from source tasks/desktop.py rather than apps.py and must
still have an application producer before theme/desktop consumers run:

| ID | Producer and selection | Runtime contract |
| --- | --- | --- |
| terminator | application-suite, required hyprland-core profile | terminator and remotinator from native Terminator package |
| python3-configobj | dependency of terminator, observed/validated by application-suite | configobj import with native Python |
| python3-gi and GTK/VTE introspection | native Terminator dependencies, desktop may independently require GI for its menus | required imports/introspection versions verified; no duplicated config ownership |
| xfe | application-suite, hyprland-core profile | native xfe executable for source file-manager entry |

The core profile selection is explicit when preparing the requested source
Hyprland experience. It does not force optional client apps or KDE changes.
Native apt metadata for terminator2.1.5-1 declares python3-configobj, python3-gi,
Cairo/DBus and GTK/VTE introspection dependencies. Actual guarded resolution and
runtime imports remain implementation checks.

Owner-directed backlog takes precedence over earlier optional office/client route discussion. See docs/backlog.md.
