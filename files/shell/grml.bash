# Managed by t2-mac-kde (shell-user-tools). grml-inspired bash, ported from
# debian-hypr files/bash/grml.bash. History settings live in history.bash.
[[ $- == *i* ]] || return 0

# --- shell options (grml: auto_cd, correct, extended globbing) -----------------
shopt -s autocd cdspell dirspell globstar extglob checkwinsize no_empty_cmd_completion

# --- completion -------------------------------------------------------------------
if ! declare -F _init_completion >/dev/null && [ -r /usr/share/bash-completion/bash_completion ]; then
  . /usr/share/bash-completion/bash_completion
fi

# --- colours ------------------------------------------------------------------------
command -v dircolors >/dev/null && eval "$(dircolors -b)"
alias ls='ls --color=auto -F'
alias grep='grep --color=auto'
alias diff='diff --color=auto'
alias ip='ip -color=auto'
alias k=kubectl   # completion: ~/.local/share/bash-completion/completions/k
alias dl='aria2c'  # parallel downloads, defaults in ~/.config/aria2/aria2.conf
alias leftbar='t2-leftstrip --panel'   # KDE: left strip panel again after a theme change

# Keyboard layout shortcuts only in a Hyprland session with hypr-kbd; in KDE/X11
# setxkbmap and the KDE keyboard settings keep their native behavior.
if [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ] && command -v hypr-kbd >/dev/null; then
  alias kbus='hypr-kbd us' kbde='hypr-kbd de'
  setxkbmap() {
    case "$*" in
      us|"us -variant "*) hypr-kbd us ;;
      de|"de nodeadkeys"|"de -variant nodeadkeys") hypr-kbd de ;;
      *) command setxkbmap "$@" ;;
    esac
  }
fi

# --- grml aliases -------------------------------------------------------------------
alias l='ls -lF'
alias la='ls -la'
alias ll='ls -l'
alias lh='ls -hAl'
alias lsd='ls -d */'
alias da='du -sch'
alias j='jobs -l'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias d='dirs -v'
alias hist='history | grep --'

# --- directory stack like grml's auto_pushd: cd remembers, cd -N jumps back -------------
DIRSTACKSIZE=20
cd() {
  local rc
  if [ "$#" -eq 1 ] && [[ $1 =~ ^-[0-9]+$ ]]; then
    builtin pushd "+${1#-}" >/dev/null
  elif [ "$#" -eq 0 ]; then
    builtin pushd "$HOME" >/dev/null
  else
    builtin pushd "$@" >/dev/null
  fi
  rc=$?
  # bash ignores DIRSTACKSIZE: drop the oldest entries ourselves
  while [ "${#DIRSTACK[@]}" -gt "$DIRSTACKSIZE" ]; do builtin popd -n -0 >/dev/null || break; done
  return "$rc"
}

# --- grml functions ------------------------------------------------------------------
mkcd() { mkdir -p -- "$1" && cd -- "$1"; }                 # make dir and enter it
cdt()  { cd "$(mktemp -d)" && pwd; }                        # cd into a fresh temp dir
bk()   { local f; for f in "$@"; do cp -a -- "$f" "$f.bak.$(date +%Y%m%dT%H%M%S)" || return; done; }  # backup copy
sll()  { local f; for f in "$@"; do while [ -L "$f" ]; do ls -l -- "$f"; f=$(readlink -- "$f"); done; ls -l -- "$f"; done; }  # follow symlinks
ssearch() { grep -rn --color=auto -- "$1" "${2:-.}"; }      # search recursively

# Add a prompt hook once; works with scalar and array PROMPT_COMMAND.
__t2_prompt_hook() {
  local hook=$1 x
  if [[ "$(declare -p PROMPT_COMMAND 2>/dev/null)" == "declare -a"* ]]; then
    for x in "${PROMPT_COMMAND[@]}"; do [ "$x" = "$hook" ] && return 0; done
    PROMPT_COMMAND=("$hook" "${PROMPT_COMMAND[@]}")
  else
    case "; ${PROMPT_COMMAND:-}; " in *"; $hook; "*) return 0 ;; esac
    PROMPT_COMMAND="$hook${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
  fi
}

# --- prompt: user@host cwd (git) $, red user for root, red exit code on failure ---------
[ -r /usr/lib/git-core/git-sh-prompt ] && . /usr/lib/git-core/git-sh-prompt
GIT_PS1_SHOWDIRTYSTATE=1
GIT_PS1_SHOWUNTRACKEDFILES=1
__grml_prompt() {
  local rc=$?
  local blue='\[\e[1;34m\]' red='\[\e[1;31m\]' yellow='\[\e[0;33m\]' bold='\[\e[1m\]' off='\[\e[0m\]'
  local user="$blue\u$off"; [ "$EUID" -eq 0 ] && user="$red\u$off"
  local code=""; [ "$rc" -ne 0 ] && code="$red$rc$off "
  local git=""; declare -F __git_ps1 >/dev/null && git="$yellow$(__git_ps1 ' (%s)')$off"
  # Short tmux-style terminal/tab title: current directory name only
  local title="\[\e]0;\W\a\]"
  PS1="$title$code$user@\h $bold\w$off$git \\$ "
  return "$rc"
}
__t2_prompt_hook __grml_prompt
