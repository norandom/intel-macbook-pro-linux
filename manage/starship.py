"""Starship prompt for bash and fish (config shell_prompt = "starship").

One ~/.config/starship.toml for both shells: the grml layout (exit code, user@host, directory,
git) plus language symbols that appear only where they apply (Python venv next to a
pyproject.toml, Node next to package.json, ...), command duration on the right. Colours come
from the five terminal palettes; hypr-termtheme rewrites the `palette = "..."` line and starship
reads its config at every prompt, so SUPER+Y recolours the next prompt.
"""
from __future__ import annotations

import re

from manage.fish_shell import palette_roles

THEMES = ("cobalt", "navy", "fixedsys", "cream", "petrol")
MARKER = "Managed by t2-mac-kde"

BASHRC_MARKER = "# {mark} t2-mac-kde: starship prompt"
# After the grml block: starship takes over PS1 (it still runs the other prompt hooks, e.g.
# history sync and the fish hand-over, inside its own). Title as grml: the directory name.
BASHRC = r'''if [[ $- == *i* ]] && command -v starship >/dev/null; then
  __grml_prompt() { return $?; }
  # VTE terminals (Terminator, xfce4-terminal) set "user@host:path" as the title in their hook,
  # which now runs after ours: keep their status/cwd reports, drop only that title.
  if declare -F __vte_osc7 >/dev/null && declare -F __vte_termprop_set >/dev/null; then
    __vte_prompt_command() { local rc=$?; __vte_termprop_set "vte.shell.postexec" "$rc"; __vte_osc7; return $rc; }
  fi
  __t2_title() { printf '\e]0;%s\a' "${PWD##*/}"; }
  starship_precmd_user_func=__t2_title
  eval "$(starship init bash)"
fi'''

FISH = "command -q starship; and starship init fish | source"

# Language and tool modules shown when the directory calls for them.
LANGS = ("python", "nodejs", "rust", "golang", "nim", "c", "java", "lua", "ruby", "zig", "deno", "bun")

_BODY = r'''"$schema" = "https://starship.rs/config-schema.json"
add_newline = false
command_timeout = 800
palette = "{palette}"

format = """$status$username$hostname$directory$git_branch$git_state$git_status\
{langs}$nix_shell$container$jobs$character"""
right_format = "$cmd_duration"

[status]
disabled = false
format = "[$status]($style) "
style = "bold err"

[username]
show_always = true
format = "[$user]($style)@"
style_user = "bold user"
style_root = "bold err"

[hostname]
ssh_only = false
format = "[$hostname]($style) "
style = "fg"

[directory]
truncation_length = 0
truncate_to_repo = false
style = "bold fg"
read_only = " 󰌾"
read_only_style = "err"
format = "[$path]($style)[$read_only]($read_only_style) "

[git_branch]
symbol = " "
style = "git"
format = "[$symbol$branch(:$remote_branch)]($style) "

[git_status]
style = "git"
format = "([$all_status$ahead_behind]($style) )"

[git_state]
style = "bold err"

[cmd_duration]
min_time = 2000
style = "dim"
format = "[$duration]($style)"

[jobs]
style = "dim"

[character]
success_symbol = '[\$](bold fg)'
error_symbol = '[\$](bold err)'

[nix_shell]
symbol = " "
style = "lang"
format = "[$symbol$state( \\($name\\))]($style) "

[container]
style = "dim"

[python]
symbol = " "
style = "lang"
format = '[${symbol}${pyenv_prefix}(${version} )(\($virtualenv\) )]($style)'

[nodejs]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"

[rust]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"

[golang]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"

[nim]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"

[c]
symbol = " "
style = "lang"
format = "[$symbol($version(-$name) )]($style)"

[java]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"

[lua]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"

[ruby]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"

[zig]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"

[deno]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"

[bun]
symbol = " "
style = "lang"
format = "[$symbol($version )]($style)"
'''


def palette_table(name: str, ini_text: str) -> str:
    r = palette_roles(ini_text)
    pal = r["pal"]
    roles = {"fg": r["fg"], "dim": r["dim"], "err": pal[1], "user": pal[4], "git": pal[3], "lang": pal[6]}
    return f"\n[palettes.{name}]\n" + "".join(f'{k} = "#{v}"\n' for k, v in roles.items())


def config(palettes: dict[str, str], current: str) -> str:
    """palettes: theme name -> foot theme ini text; current: the active theme."""
    if current not in palettes:
        current = next(iter(palettes))
    head = (f"# {MARKER} (config shell_prompt = \"starship\"; manage/starship.py).\n"
            "# The palette line follows the terminal theme (hypr-termtheme, SUPER+Y).\n"
            "# Changes here are overwritten by tasks/shell.py; keep your own in a fork of manage/starship.py.\n")
    body = _BODY.replace("{palette}", current).replace("{langs}", "".join(f"${m}" for m in LANGS))
    return head + body + "".join(palette_table(n, t) for n, t in palettes.items())


_PALETTE_LINE = re.compile(r'^palette = "[^"]*"$', re.M)


def switch_palette(text: str, name: str) -> str:
    """The config with another active palette (only the palette line changes)."""
    return _PALETTE_LINE.sub(f'palette = "{name}"', text, count=1)
