# Managed by t2-mac-kde. Loaded after fzf so Atuin owns Ctrl+R.
command -q zoxide; and zoxide init fish | source
if command -q atuin
    # Enforce the local-only policy even if inherited settings say otherwise.
    set -gx ATUIN_AUTO_SYNC false
    set -gx ATUIN_UPDATE_CHECK false
    set -gx ATUIN_SYNC_ADDRESS http://127.0.0.1:9
    set -gx ATUIN_DAEMON__ENABLED false
    atuin init fish --disable-up-arrow | source
end

function y --description 'Browse files and return to the selected directory'
    command -q yazi; or return 127
    set -l tmp (command mktemp -t yazi-cwd.XXXXXX); or return
    command yazi $argv --cwd-file="$tmp"
    set -l rc $status
    set -l cwd
    if read -z cwd < "$tmp"; and test -d "$cwd"; and test "$cwd" != "$PWD"
        cd -- "$cwd"
    end
    command rm -f -- "$tmp"
    return $rc
end

function ff --description 'Find files with a syntax-highlighted preview'
    command -q fzf; and command -q fd; and command -q bat; or return 127
    command fd --type f --hidden --exclude .git --print0 $argv | command fzf --read0 \
        --preview 'bat --color=always --style=numbers --line-range=:300 -- {}'
end
