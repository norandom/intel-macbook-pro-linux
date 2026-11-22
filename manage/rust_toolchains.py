"""Rust toolchains outside the Nix environment.

nixpkgs' rustup patches every toolchain it downloads (patchelf) to run on Nix's glibc. The
compiler then loads build scripts and proc-macros that the system linker built against the
system glibc, and the weekly Nix garbage collection can remove that glibc. rustup now comes
from the Ubuntu archive, which keeps rust-lang.org toolchains as they are built. Toolchains
that the Nix rustup patched are reinstalled once with the same components; the default
toolchain stays the default.
"""

SYSTEM_RUSTUP = "/usr/bin/rustup"

REINSTALL_PATCHED = r"""set -eu
r=${T2_RUSTUP:-/usr/bin/rustup}   # T2_RUSTUP: tests only
[ -x "$r" ] || exit 0
home=${RUSTUP_HOME:-$HOME/.rustup}
[ -d "$home/toolchains" ] || exit 0
default=$("$r" default 2>/dev/null | cut -d' ' -f1 || true)
for dir in "$home"/toolchains/*/; do
  tc=$(basename "$dir")
  rustc="$dir/bin/rustc"
  [ -x "$rustc" ] || continue
  readelf -l "$rustc" 2>/dev/null | grep -q 'interpreter: /nix/store/' || continue
  host=${tc#*-}
  comps=$("$r" component list --installed --toolchain "$tc" | sed "s/-$host\$//" \
          | grep -vxE 'rustc|cargo|rust-std|rust-docs' | sed 's/^/-c /' | tr '\n' ' ')
  echo "reinstalling $tc (was patched to Nix's glibc) ${comps:+with $comps}"
  "$r" toolchain uninstall "$tc"
  # shellcheck disable=SC2086  # one word per -c option
  "$r" toolchain install "$tc" --profile minimal $comps
done
[ -n "$default" ] && "$r" default "$default" >/dev/null || true
"""

