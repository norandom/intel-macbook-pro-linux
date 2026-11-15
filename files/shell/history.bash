# Managed by t2-mac-kde (shell-user-tools). Kali-style large, shared, timestamped history.
[[ $- == *i* ]] || return 0
HISTSIZE=100000
HISTFILESIZE=200000
HISTCONTROL=ignoreboth:erasedups
HISTTIMEFORMAT='%F %T  '
HISTIGNORE='ls:ll:cd:pwd:bg:fg:clear:history:exit'
shopt -s histappend cmdhist
# Every terminal sees the others' commands immediately (like zsh share_history).
# Keeps $? so the prompt still shows the previous command's status.
__t2_history_sync() { local rc=$?; history -a; history -n; return "$rc"; }
declare -F __t2_prompt_hook >/dev/null && __t2_prompt_hook __t2_history_sync
