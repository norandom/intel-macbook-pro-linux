# Upstream maintainer release direction

Explicit owner instruction: use the hypr-rdp maintainer's GitHub release package.
Do not use norandom's patched .deb or plan a local RDP source build.

Repository: https://github.com/MuNeNiCK/hypr-rdp
Candidate latest observed release: v0.1.8.
Asset: hypr-rdp-v0.1.8-x86_64-linux.tar.gz
URL: https://github.com/MuNeNiCK/hypr-rdp/releases/download/v0.1.8/hypr-rdp-v0.1.8-x86_64-linux.tar.gz
Size: 8936327 bytes.
GitHub-reported SHA256: f8b324fcf5c169dd4df269685294db55078b4d6a28cd47a6a86e00d35671b0fd.
These are release API metadata, not a downloaded or verified local artifact.

v0.1.7 release notes include norandom's ClearCodec frame-selection contribution
(PR108), restored authenticated session hooks and STRING-only clipboard support.
Do not blindly carry source-fork patches or source log-parsing workarounds into
upstream. Evaluate needed behavior against current upstream options/hooks.

Upstream tagged v0.1.8 README still declares Hyprland0.54+. The owner's chosen
native desktop backport baseline is Ubuntu0.53.3. Record the discrepancy and
require explicit runtime compatibility evidence; do not claim support from the
binary's presence or configuration backport alone. Do not silently switch to an
older/security-unreviewed release, replace the compositor or build a fork.

Upstream binary runtime dependencies include libva, PipeWire, libxkbcommon,
Linux-PAM and Wayland libraries. Validate actual ELF/ABI dependencies during
artifact verification before installation; release metadata is not that check.
The binary has not been downloaded/run by this session. The attempted fork .deb
download was cancelled by the owner and no candidate file is present.

Upstream configured authentication allows unauthenticated connections if
credentials are omitted, so require an explicit authenticated configuration
before listener activation. Keep local audio/mic/camera support, source keyboard
mapping and session scoping. Audio mirror/off are available upstream; avoid
forcing source VM redirect/console blanking behavior. No PAM/system-auth changes
are implied by preferring the packaged server; configured credentials can remain
feature-local, subject to the eventual requirement/design contract.

## Additional tagged source inspection

Fetched v0.1.8 src/hyprland.rs and monitor_ipc_tests.rs. Monitor rules prefer
Lua eval but fall back to legacy `keyword monitor` after delivered parser
rejection; upstream tests exercise the fallback. This is useful evidence for
the older desktop API path, not proof of full0.53 runtime compatibility.
The release workflow builds on ubuntu-latest and publishes a tar.gz. Actual
runtime library versions remain to be checked from the selected artifact.
Source files are available in /tmp/t2-hypr-rdp-upstream for this session.
