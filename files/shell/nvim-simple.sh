#!/usr/bin/env bash
# Managed by t2-mac-kde (shell-user-tools). Install nvim-simple (CUA keys, menu bar,
# Berg theme) at a pinned commit with pinned plugins.
#   nvim-simple.sh <commit> <owner/repo=commit>...
# Builds and verifies in a staging XDG home first; ~/.config/nvim is only touched
# when every plugin is checked out at its pinned commit. A non-nvim-simple config is
# moved to ~/.config/nvim.backup-<timestamp>. The coordinated-themes file
# plugin/debian-hypr-theme.lua is left in place.
set -euo pipefail
rev=$1; shift
cfg=${XDG_CONFIG_HOME:-$HOME/.config}/nvim
stamp="$rev $*"
theme=plugin/debian-hypr-theme.lua

[ "$(cat "$cfg/.nvim-simple" 2>/dev/null)" = "$stamp" ] && { echo "nvim-simple already at $rev"; exit 0; }
command -v nvim >/dev/null || { echo "nvim not installed (application-suite/tools.py)" >&2; exit 1; }

t=$(mktemp -d)
trap 'rm -rf "$t"' EXIT
git -C "$t" init -q src
git -C "$t/src" fetch -q --depth 1 https://github.com/norandom/nvim-simple.git "$rev"
git -C "$t/src" checkout -q FETCH_HEAD
[ "$(git -C "$t/src" rev-parse HEAD)" = "$rev" ] || { echo "nvim-simple: fetched wrong revision" >&2; exit 1; }

stage=$t/config/nvim
mkdir -p "$t/config" "$t/data" "$t/state" "$t/cache"
cp -r "$t/src/nvim" "$stage"
# vim-plug is vendored at this revision; never let init.vim fetch it from master.
[ -s "$stage/autoload/plug.vim" ] || { echo "nvim-simple: vendored plug.vim missing" >&2; exit 1; }
for pin in "$@"; do
  repo=${pin%%=*} commit=${pin#*=}
  grep -qxF "Plug '$repo'" "$stage/init.vim" || { echo "nvim-simple: plugin $repo not in init.vim" >&2; exit 1; }
  sed -i "s|^Plug '$repo'\$|Plug '$repo', { 'commit': '$commit' }|" "$stage/init.vim"
done

log=$t/plug.log
XDG_CONFIG_HOME=$t/config XDG_DATA_HOME=$t/data XDG_STATE_HOME=$t/state XDG_CACHE_HOME=$t/cache \
  timeout 600 nvim --headless -i NONE "+PlugInstall --sync" "+qall" >"$log" 2>&1 \
  || { cat "$log" >&2; echo "nvim-simple: headless PlugInstall failed" >&2; exit 1; }
for pin in "$@"; do
  repo=${pin%%=*} commit=${pin#*=}
  have=$(git -C "$stage/plugged/${repo#*/}" rev-parse HEAD 2>/dev/null || true)
  [ "$have" = "$commit" ] || { cat "$log" >&2; echo "nvim-simple: $repo at '${have:-missing}', want $commit" >&2; exit 1; }
done
# Second headless start must load cleanly (no errors from init.vim or plugins).
out=$(XDG_CONFIG_HOME=$t/config XDG_DATA_HOME=$t/data XDG_STATE_HOME=$t/state XDG_CACHE_HOME=$t/cache \
  timeout 60 nvim --headless -i NONE "+lua if vim.fn.exists('*ToggleTheme')==0 or vim.fn.exists(':NERDTree')==0 then io.stderr:write('nvim-simple: ToggleTheme/NERDTree missing\n') end" "+qall" 2>&1) \
  || { echo "$out" >&2; exit 1; }
[ -z "$out" ] || { echo "$out" >&2; echo "nvim-simple: startup produced errors" >&2; exit 1; }
echo "$stamp" >"$stage/.nvim-simple"

# Publish. Existing foreign config (e.g. LazyVim) is kept as a unique backup.
if [ -e "$cfg" ] && [ ! -e "$cfg/.nvim-simple" ]; then
  backup="$cfg.backup-$(date +%Y%m%dT%H%M%S)"
  mv "$cfg" "$backup"
  echo "previous ~/.config/nvim moved to $backup"
  if [ -e "$backup/$theme" ]; then mkdir -p "$cfg/plugin"; mv "$backup/$theme" "$cfg/$theme"; fi
fi
mkdir -p "$cfg"
for f in init.vim lua colors autoload plugged; do
  rm -rf "$cfg/$f.new"; cp -r "$stage/$f" "$cfg/$f.new"
done
for f in init.vim lua colors autoload plugged; do
  rm -rf "$cfg/$f"; mv "$cfg/$f.new" "$cfg/$f"
done
cp "$stage/.nvim-simple" "$cfg/.nvim-simple"
echo "nvim-simple $rev installed in $cfg"
