# Inactive prototype companion; not deployed or sourced. For extraction to a separate project.
# Terminator plugin consumes only this prefix; ordinary title changes are ignored.
function __t2_command_header --on-event fish_preexec
    set -q TERMINATOR_UUID; or return
    set -l text (string replace -ar '[[:cntrl:]]' ' ' -- "$argv[1]")
    set -g __t2_prompt_ready 0
    set -g __t2_last_command "$text"
    printf '\e]0;T2CMD:%s\a' "$text"
end

# Signal readiness only at a real fish prompt, never while a program owns the PTY.
function __t2_command_ready --on-event fish_prompt
    set -q TERMINATOR_UUID; or return
    set -g __t2_prompt_ready 1
    set -l directory (string replace -ar '[[:cntrl:]]' ' ' -- "$PWD")
    printf '\e]0;T2READY:%s\a' "$directory"
end

function fish_title
    if set -q TERMINATOR_UUID; and test "$__t2_prompt_ready" = 1
        printf 'T2READY:%s' (string replace -ar '[[:cntrl:]]' ' ' -- "$PWD")
    else if set -q TERMINATOR_UUID; and set -q __t2_last_command
        printf 'T2CMD:%s' "$__t2_last_command"
    else
        basename -- $PWD
    end
end
