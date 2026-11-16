#!/usr/bin/env bash
# Managed by t2-mac-kde (shell-user-tools). Regenerate Bash completions from the
# installed kubectl / helm / gh / ax / rc. Each file is written to a temp file,
# syntax-checked and only then moved into place. Files without our header
# (written by the owner or another tool) are never replaced or removed.
set -u
dir=${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions
header='# Managed by t2-mac-kde shell-user-tools'
mkdir -p "$dir"
PATH="$HOME/.nix-profile/bin:$HOME/.local/bin:$PATH"

ours() { [ ! -e "$1" ] || head -n1 "$1" 2>/dev/null | grep -qxF "$header"; }

publish() {  # name, then the generator command
  local name=$1 target="$dir/$1" tmp; shift
  if ! ours "$target"; then echo "$name: kept unmanaged $target"; return 0; fi
  tmp=$(mktemp "$dir/.$name.XXXXXX") || return 1
  if { echo "$header"; "$@"; } >"$tmp" 2>/dev/null && [ "$(wc -l <"$tmp")" -gt 1 ] && bash -n "$tmp"; then
    chmod 644 "$tmp" && mv -f "$tmp" "$target" && echo "$name: ok"
  else
    rm -f "$tmp" "$target"; echo "$name: unavailable (generator failed)"
  fi
}

drop() { if ours "$dir/$1" && [ -e "$dir/$1" ]; then rm -f "$dir/$1"; fi; echo "$1: unavailable (not installed)"; }

k_alias() { kubectl completion bash && echo 'declare -F __start_kubectl >/dev/null && complete -o default -F __start_kubectl k'; }

if command -v kubectl >/dev/null; then publish kubectl kubectl completion bash; publish k k_alias; else drop kubectl; drop k; fi
if command -v helm >/dev/null; then publish helm helm completion bash; else drop helm; fi
if command -v gh >/dev/null; then publish gh gh completion -s bash; else drop gh; fi
if command -v ax >/dev/null; then publish ax ax completion bash; else drop ax; fi
if command -v rc >/dev/null; then publish rc rc completions bash; else drop rc; fi
exit 0
