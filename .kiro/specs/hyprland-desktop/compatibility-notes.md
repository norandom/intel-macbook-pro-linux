# Native backport compatibility evidence

The owner explicitly chose backporting newer source config/helper behavior to
native Ubuntu Hyprland, prioritizing original decorations. Newer compositor
source builds and their provisional closure blocker are superseded.

Read-only apt metadata identifies Hyprland0.53.3+ds-4 providing
hyprland-abi-6d24081 and hyprbars0.53.0-1 depending on that exact ABI token.
The current source is Lua0.56, so direct copying is invalid. Design.md maps its
settings/actions to0.53 conf/dispatch/JSON and a session worker for callbacks.
Primary0.53.3 compositor source and corresponding official plugin README were
fetched through GitHub plugin. Local metadata is compatibility evidence, not
proof packages are installed or live graphics/audio/input have passed.

Native uwsm0.25.2, Waybar0.15, Mako1.10, Fuzzel1.12, portal1.3.11 and
cliphist0.5 candidates are recorded in research.md. Discover plugin path from
actual package-owned files rather than copy a Debian ABI path. No package
transaction may cross protected-system-boundary, even indirectly through hooks.

Desktop status exposes the actual native0.53 identity for RDP consumers. The
maintainer's chosen upstream hypr-rdp release may require0.54+; that is an
RDP-specific compatibility gate, not permission to change compositor generation
or resurrect source builds. No RDP implementation is owned here.
