"""fish as the interactive shell in every terminal (config shell_interactive = "fish").

Bash stays the login shell. Interactive bash runs ~/.bashrc as before (PATH with Nix first,
nvm's Node, system alerts) and hands over to fish at its first prompt, so fish inherits
that environment. What doesn't inherit (aliases, functions, the prompt) is generated here from
the same sources bash uses: files/shell/grml.bash, the safe-chain tool list, turbo.bash.

Stays bash: `bash` typed in fish, T2_NO_FISH=1, scripts, `bash -c`, no terminal.
"""
from __future__ import annotations

import re
import shlex

MARKER = "# {mark} t2-mac-kde: fish in interactive terminals"
# Runs at bash's first prompt (PROMPT_COMMAND), i.e. after every other ~/.bashrc block.
BASHRC = r'''if [[ $- == *i* && -z ${BASH_EXECUTION_STRING-} && -t 0 && -t 1 && ${TERM_PROGRAM-} != WarpTerminal && ${T2_NO_FISH-} != 1 && -x /usr/bin/fish ]] \
   && [[ $(ps -o comm= -p "$PPID" 2>/dev/null) != fish ]]; then
  __t2_fish() { if shopt -q login_shell; then exec /usr/bin/fish --login; else exec /usr/bin/fish; fi; }
  if [[ "$(declare -p PROMPT_COMMAND 2>/dev/null)" == "declare -a"* ]]; then
    PROMPT_COMMAND+=(__t2_fish)
  else
    PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND; }__t2_fish"
  fi
fi'''

CONF = "~/.config/fish/conf.d/t2-mac-kde.fish"

# grml.bash alias -> fish. Abbreviations expand as you type (you see the real command);
# plain wrappers stay aliases.
ABBR = {
    "l": "ls -lF", "la": "ls -la", "ll": "ls -l", "lh": "ls -hAl", "lsd": "ls -d */",
    "da": "du -sch", "j": "jobs", "d": "dirh", "hist": "history search --contains",
    "k": "kubectl", "dl": "aria2c", "leftbar": "t2-leftstrip --panel",
    "craftup": "t2-craft-update",
}
WRAP = {"ls": "ls --color=auto -F", "grep": "grep --color=auto", "diff": "diff --color=auto",
        "ip": "ip -color=auto"}
# Bash aliases with a native fish equivalent (not ported 1:1).
NATIVE = {"..", "...", "....", "kbus", "kbde"}

BODY = r'''
status is-interactive; or return
set -g fish_greeting
# pyinfra: run without "Press enter to execute..." (owner request); --dry still only previews.
set -gx PYINFRA_YES 1

# --- grml-style colours and abbreviations ---------------------------------------------------
{wraps}
{abbrs}
# .. ... ....: up one, two, three directories
function __t2_multicd
    echo cd (string repeat -n (math (string length -- $argv[1]) - 1) ../)
end
abbr --add __t2_dotdot --regex '^\.\.+$' --function __t2_multicd
# Ghostty integration (ssh terminfo/env, sudo, cursor): Ghostty injects it only into the shell it
# starts, which is bash; after the hand-over to fish, load it here.
if set -q GHOSTTY_RESOURCES_DIR; and not functions -q __ghostty_setup
    set -l gi $GHOSTTY_RESOURCES_DIR/shell-integration/fish/vendor_conf.d/ghostty-shell-integration.fish
    test -r $gi; and source $gi
end
# bash's !!: expands to the previous command line (sudo !! -> sudo <last command>)
function __t2_last_history_item
    echo $history[1]
end
abbr --add !! --position anywhere --function __t2_last_history_item

# --- directory history: cd -N goes N directories back (grml auto_pushd); cdh, prevd, nextd --
if not functions -q __t2_fish_cd
    functions -q cd; and functions --copy cd __t2_fish_cd
end
function cd --wraps cd --description 'cd; cd -N: N directories back'
    if test (count $argv) -eq 1; and string match -qr '^-[0-9]+$' -- $argv[1]
        prevd (string sub -s 2 -- $argv[1])
    else if functions -q __t2_fish_cd
        __t2_fish_cd $argv
    else
        builtin cd $argv
    end
end

# --- grml functions -----------------------------------------------------------------------
function mkcd --description 'make a directory and enter it'
    mkdir -p -- $argv[1]; and cd -- $argv[1]
end
function cdt --description 'cd into a fresh temp directory'
    cd (mktemp -d); and pwd
end
function bk --description 'timestamped backup copy'
    for f in $argv
        cp -a -- $f $f.bak.(date +%Y%m%dT%H%M%S); or return
    end
end
function sll --description 'follow symlinks'
    for f in $argv
        while test -L $f
            ls -l -- $f
            set f (readlink -- $f)
        end
        ls -l -- $f
    end
end
function ssearch --description 'search recursively'
    set -l where .
    set -q argv[2]; and set where $argv[2]
    grep -rn --color=auto -- $argv[1] $where
end

# --- keyboard layout (Hyprland session only) ---------------------------------------------
if set -q HYPRLAND_INSTANCE_SIGNATURE; and command -q hypr-kbd
    abbr --add kbus 'hypr-kbd us'
    abbr --add kbde 'hypr-kbd de'
    function setxkbmap --wraps setxkbmap
        switch "$argv"
            case us 'us -variant *'
                hypr-kbd us
            case de 'de nodeadkeys' 'de -variant nodeadkeys'
                hypr-kbd de
            case '*'
                command setxkbmap $argv
        end
    end
end

# --- turbo-on / turbo-off / turbo-status (laptop-resource-policy) ----------------------------
test -r ~/.config/t2-mac-kde/turbo.bash
and string match -r "^alias [A-Za-z0-9_-]+='[^']*'\$" < ~/.config/t2-mac-kde/turbo.bash | source

# --- Intel oneAPI on request (GCC stays the default; bash: the same functions) ---------------
if test -x /opt/intel/oneapi/compiler/latest/bin/icx
    function intel --description 'run one command with Intel icx/icpx as CC/CXX'
        env CC=icx CXX=icpx PATH=(string join : $PATH /opt/intel/oneapi/compiler/latest/bin) $argv
    end
    function nim-icx --wraps nim --description 'nim, compiling through Intel icx/icpx'
        env PATH=(string join : $PATH /opt/intel/oneapi/compiler/latest/bin) nim --cc:clang --clang.exe=icx --clang.linkerexe=icx --clang.cpp.exe=icpx --clang.cpp.linkerexe=icpx $argv
    end
end

# --- Debian package builds always with GCC (bash: the same functions) ------------------------
function dpkg-buildpackage --wraps dpkg-buildpackage
    CC=gcc CXX=g++ command dpkg-buildpackage $argv
end
function debuild --wraps debuild
    CC=gcc CXX=g++ command debuild $argv
end
{safe_chain}
# --- nvm is a bash function: run it in bash ("nvm use" only lasts for that bash) -------------
function nvm --description 'nvm, via bash'
    bash -c '. "$NVM_DIR/nvm.sh" --no-use; nvm "$@"' nvm $argv
end

# --- fzf: Ctrl+R history, Ctrl+T insert a file, Alt+C cd into a directory ---------------------
command -q fzf; and fzf --fish | source
set -l t2_navigation $__fish_config_dir/t2-navigation.fish
test -r "$t2_navigation"; and source "$t2_navigation"

# --- prompt: user@host cwd (git) $, red user for root, red exit code on failure --------------
# Colours come from the terminal palette (hypr-termtheme sets fish_color_* / t2_color_*).
set -q t2_color_git; or set -g t2_color_git yellow
set -q t2_color_duration; or set -g t2_color_duration brblack
for v in fish_color_status fish_color_user fish_color_host fish_color_cwd fish_color_cwd_root
    set -q $v; or set -g $v normal
end
set -g __fish_git_prompt_showdirtystate 1
set -g __fish_git_prompt_showuntrackedfiles 1
function fish_prompt
    set -l rc $status
    test $rc -ne 0; and printf '%s%s%s ' (set_color $fish_color_status) $rc (set_color normal)
    set -l who $fish_color_user
    fish_is_root_user; and set who $fish_color_cwd_root
    printf '%s%s%s@%s%s%s %s%s%s' (set_color $who) $USER (set_color normal) \
        (set_color $fish_color_host) (prompt_hostname) (set_color normal) \
        (set_color $fish_color_cwd) (prompt_pwd --full-length-dirs 99) (set_color normal)
    printf '%s%s%s' (set_color $t2_color_git) (fish_git_prompt) (set_color normal)
    fish_is_root_user; and echo -n ' # '; or echo -n ' $ '
end
# Tab/window title: the running program (claude, nvim, ssh, ...); the directory while idle
function fish_title
    set -l cmd (string split -n -f1 -- ' ' (string trim -- "$argv[1]"))
    if test -n "$cmd"
        path basename -- $cmd
    else
        basename -- $PWD
    end
end

# --- how long the last command took (right side, from 2 s) ---------------------------------
function __t2_duration --argument-names ms
    set -l s (math -s0 $ms / 1000)
    if test $s -ge 3600
        printf '%dh%02dm' (math -s0 $s / 3600) (math -s0 "$s % 3600 / 60")
    else if test $s -ge 60
        printf '%dm%02ds' (math -s0 $s / 60) (math $s % 60)
    else if test $ms -ge 10000
        printf '%ds' $s
    else
        printf '%.1fs' (math $ms / 1000)
    end
end
function fish_right_prompt
    set -q CMD_DURATION; and test "$CMD_DURATION" -ge 2000; or return
    printf '%s%s%s' (set_color $t2_color_duration) (__t2_duration $CMD_DURATION) (set_color normal)
end

# --- done: notification when a command ran >= 30 s and its terminal isn't focused ------------
set -g t2_done_after 30000
set -g t2_done_skip nvim vim vi nano less more man ssh mosh sftp lftp btop htop atop top watch tail \
    multitail lazygit k9s ktop zellij byobu tmux screen fzf glow posting trip euporie claude codex \
    copilot python python3 ipython node bash fish sudoedit
function __t2_terminal_focused
    set -l apid (hyprctl activewindow -j 2>/dev/null | string match -rg '"pid": (\d+)')
    test -n "$apid"; or return 1
    set -l p $fish_pid
    while test -n "$p"; and test "$p" -gt 1
        test "$p" = "$apid"; and return 0
        set p (string trim -- (ps -o ppid= -p $p 2>/dev/null))
    end
    return 1
end
function __t2_done --on-event fish_postexec
    set -l rc $status
    test "$CMD_DURATION" -ge $t2_done_after; or return
    set -q HYPRLAND_INSTANCE_SIGNATURE; and command -q notify-send; or return
    set -l words (string split -n ' ' -- (string trim -- $argv[1]))
    test "$words[1]" = sudo; and set -e words[1]
    contains -- (path basename -- "$words[1]") $t2_done_skip; and return
    __t2_terminal_focused; and return
    set -l head "Done"
    set -l urgency normal
    if test $rc -ne 0
        set head "Failed ($rc)"
        set urgency critical
    end
    command notify-send -a fish -u $urgency "$head after "(__t2_duration $CMD_DURATION) \
        (string shorten -m 120 -- $argv[1]) >/dev/null 2>&1
end
'''


def grml_aliases(text: str) -> set[str]:
    """Names defined by alias lines, including several on one line (alias a='x' b='y')."""
    return {w.split("=", 1)[0] for line in re.findall(r"^\s*alias (.+)$", text, re.M)
            for w in shlex.split(line, comments=True) if "=" in w}


def fish_conf(safe_chain_tools: tuple[str, ...] = (), starship: bool = False) -> str:
    wraps = "\n".join(f"alias {n} '{c}'" for n, c in WRAP.items())
    abbrs = "\n".join(f"abbr --add {n} '{c}'" for n, c in ABBR.items())
    sc = ""
    if safe_chain_tools:
        sc = ("\n# --- Aikido Safe Chain: malware check before package installs (config safe_chain) ----------\n"
              + "\n".join(f"command -q aikido-{t}; and alias {t} aikido-{t}" for t in safe_chain_tools) + "\n")
    wraps += r"""
# Nix supplies prefixed Rust utilities: use them only in interactive fish.
# Keep fish builtins (test, printf, ...) and allow `command cp` to select system cp.
for tool in $HOME/.nix-profile/bin/uutils-*
    test -x "$tool"; or continue
    set -l utility (string replace 'uutils-' '' -- (path basename "$tool"))
    builtin -q $utility; and continue
    alias $utility (string escape -- "$tool")
end
"""
    wraps += "\nif command -q eza\n    alias ls 'eza --icons=auto --group-directories-first'\nend"
    return ("# Managed by t2-mac-kde (config shell_interactive = \"fish\"; manage/fish_shell.py).\n"
            "# Your own settings: ~/.config/fish/config.fish or another conf.d file.\n"
            + BODY.replace("{wraps}", wraps).replace("{abbrs}", abbrs).replace("{safe_chain}", sc)
            + ("\n# --- starship prompt (config shell_prompt = \"starship\"): replaces the prompt above ---------\n"
               "command -q starship; and starship init fish | source\n" if starship else ""))


# --- palettes: fish syntax colours from the foot theme of each terminal profile ------------------
def _ini_colors(text: str) -> dict[str, str]:
    return dict(re.findall(r"^([a-z0-9-]+)=([0-9a-fA-F]{6})\s*$", text, re.M))


def _blend(a: str, b: str, t: float) -> str:
    """a*(1-t) + b*t, hex rrggbb."""
    return "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02x}" for i in (0, 2, 4))


def _light(hexcolor: str) -> bool:
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b > 140


def palette_roles(ini_text: str) -> dict:
    """Prompt colour roles of one terminal palette (fish and starship share them).
    The bright set on dark backgrounds, the regular set on light ones."""
    c = _ini_colors(ini_text)
    fg, bg = c["foreground"], c["background"]
    pal = [c[f"{'regular' if _light(bg) else 'bright'}{i}"] for i in range(8)]
    return {"fg": fg, "bg": bg, "sel": c.get("selection-background", bg), "pal": pal,
            "dim": _blend(fg, bg, 0.45)}


def palette_theme(ini_text: str, name: str) -> str:
    """fish script setting universal colour variables (running fish sessions repaint at once).
    The bright set on dark backgrounds, the regular set on light ones."""
    r = palette_roles(ini_text)
    fg, sel, pal, dim = r["fg"], r["sel"], r["pal"], r["dim"]
    colors = {
        "fish_color_normal": fg, "fish_color_command": f"{pal[3]} --bold", "fish_color_keyword": pal[5],
        "fish_color_quote": pal[2], "fish_color_param": fg, "fish_color_option": pal[6],
        "fish_color_redirection": pal[6], "fish_color_operator": pal[6], "fish_color_end": pal[5],
        "fish_color_escape": pal[6], "fish_color_error": pal[1], "fish_color_comment": dim,
        "fish_color_autosuggestion": dim, "fish_color_valid_path": "--underline",
        "fish_color_selection": f"{fg} --background={sel}", "fish_color_search_match": f"--background={sel}",
        "fish_color_history_current": "--bold", "fish_color_cancel": "--reverse",
        "fish_color_cwd": f"{fg} --bold", "fish_color_cwd_root": f"{pal[1]} --bold",
        "fish_color_user": f"{pal[4]} --bold", "fish_color_host": fg, "fish_color_host_remote": pal[3],
        "fish_color_status": f"{pal[1]} --bold",
        "fish_pager_color_prefix": f"{pal[3]} --bold", "fish_pager_color_completion": fg,
        "fish_pager_color_description": dim, "fish_pager_color_progress": f"{fg} --background={sel}",
        "fish_pager_color_selected_background": f"--background={sel}",
        "t2_color_git": pal[3], "t2_color_duration": dim,
    }
    return (f"# Managed by t2-mac-kde (coordinated-themes): fish colours for the {name} palette.\n"
            "# Applied by hypr-termtheme (SUPER+Y); universal, so open fish sessions repaint.\n"
            + "".join(f"set -U {k} {v}\n" for k, v in colors.items()))


def bash_history_to_fish(text: str, default_when: int) -> str:
    """~/.bash_history (with or without #epoch lines) -> fish_history entries, oldest first,
    duplicates kept once at their last use. Multi-line entries (after a #epoch line) stay one."""
    entries: list[tuple[str, int]] = []
    when, cur = None, []

    def flush():
        if cur:
            entries.append(("\n".join(cur), when if when is not None else default_when))

    for line in text.splitlines():
        m = re.fullmatch(r"#(\d{9,11})", line)
        if m:
            flush()
            when, cur = int(m.group(1)), []
        elif when is not None:
            cur.append(line)
        elif line.strip():
            entries.append((line, default_when))
    flush()
    last = {cmd: i for i, (cmd, _w) in enumerate(entries)}
    out = []
    for i, (cmd, w) in enumerate(entries):
        if last[cmd] != i or not cmd.strip():
            continue
        out.append(f"- cmd: {cmd.replace(chr(92), chr(92) * 2).replace(chr(10), chr(92) + 'n')}\n  when: {w}\n")
    return "".join(out)
