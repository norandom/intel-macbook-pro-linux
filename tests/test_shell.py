import os
import shutil
import subprocess
import tempfile
import re
import unittest
from pathlib import Path

from manage import shell_tools

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / 'files' / 'shell'


class ShellFragmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / 'home dir'
        (self.home / '.config/bash').mkdir(parents=True)
        for name in ('grml.bash', 'history.bash'):
            shutil.copy(SRC / name, self.home / '.config/bash' / name)
        (self.home / '.bashrc').write_text(
            'export KEEP=1\nPROMPT_COMMAND=user_hook\nuser_hook() { :; }\n' + shell_tools.BASH_INIT + '\n')

    def tearDown(self):
        self.tmp.cleanup()

    def bash(self, script, interactive=True, env=None):
        environment = {'HOME': str(self.home), 'PATH': os.environ['PATH'], 'TERM': 'dumb'}
        environment.update(env or {})
        argv = ['bash', '--norc', '--noprofile'] + (['-i'] if interactive else []) + ['-c', script]
        return subprocess.run(argv, capture_output=True, text=True, env=environment, cwd=self.home)

    def test_repeated_sourcing_keeps_hooks_once_and_status(self):
        out = self.bash('. ~/.bashrc; . ~/.bashrc; echo "PC=$PROMPT_COMMAND"; false; eval "$PROMPT_COMMAND"; '
                        'echo "RC=$?"; echo "PS1=$PS1"; echo "K=$KEEP H=$HISTSIZE"; alias k').stdout
        self.assertIn('PC=__t2_history_sync; __grml_prompt; user_hook', out)
        self.assertIn('RC=0', out)  # user_hook ran last and succeeded
        self.assertIn('K=1 H=100000', out)
        self.assertIn("alias k='kubectl'", out)
        status = self.bash('. ~/.bashrc; false; __t2_history_sync; __grml_prompt; echo "S=$?"; echo "$PS1"').stdout
        self.assertIn('S=1', status)
        self.assertIn('1', status.split('\n', 1)[1])

    def test_array_prompt_command(self):
        out = self.bash('PROMPT_COMMAND=(a b); . ~/.config/bash/grml.bash; . ~/.config/bash/grml.bash; '
                        'echo "${PROMPT_COMMAND[*]}"').stdout
        self.assertIn('__grml_prompt a b', out)

    def test_noninteractive_is_quiet_and_untouched(self):
        result = self.bash('. ~/.bashrc; echo "PC=$PROMPT_COMMAND H=${HISTSIZE:-unset}"', interactive=False)
        self.assertEqual(result.stdout.strip(), 'PC=user_hook H=unset')
        self.assertEqual(result.stderr, '')

    def test_turbo_fragment_sourced_only_when_readable(self):
        self.assertNotIn('turbo-status', self.bash('. ~/.bashrc; alias').stdout)
        turbo = self.home / '.config/t2-mac-kde/turbo.bash'
        turbo.parent.mkdir(parents=True)
        shutil.copy(REPO / 'files/resource-policy/turbo.bash', turbo)
        self.assertIn('turbo-status', self.bash('. ~/.bashrc; alias').stdout)
        turbo.chmod(0)
        if os.access(turbo, os.R_OK):
            self.skipTest('running as root')
        self.assertNotIn('turbo-status', self.bash('. ~/.bashrc; alias').stdout)

    def test_keyboard_shim_only_in_hyprland_with_hypr_kbd(self):
        out = self.bash('. ~/.bashrc; type -t setxkbmap; alias kbus').stdout
        self.assertNotIn('function', out)
        fake = self.home / 'bin'
        fake.mkdir()
        (fake / 'hypr-kbd').write_text('#!/bin/sh\necho "hypr-kbd $*"\n')
        (fake / 'hypr-kbd').chmod(0o755)
        env = {'HYPRLAND_INSTANCE_SIGNATURE': 'x', 'PATH': f'{fake}:{os.environ["PATH"]}'}
        self.assertIn('hypr-kbd de', self.bash('. ~/.bashrc; setxkbmap de nodeadkeys', env=env).stdout)

    def test_directory_stack_is_bounded(self):
        out = self.bash('. ~/.bashrc; for i in $(seq 30); do mkdir -p "d$i"; cd "d$i"; done; '
                        'echo "N=${#DIRSTACK[@]}"').stdout
        self.assertIn('N=20', out)


class CompletionTests(unittest.TestCase):
    def test_generates_checked_files_and_keeps_unmanaged(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, fake = Path(tmp) / 'home', Path(tmp) / 'bin'
            fake.mkdir()
            (fake / 'kubectl').write_text('#!/bin/sh\necho "__start_kubectl() { :; }"; echo "complete -F __start_kubectl kubectl"\n')
            (fake / 'helm').write_text('#!/bin/sh\necho "if then fi("\n')  # malformed output
            for f in fake.iterdir():
                f.chmod(0o755)
            comp = home / '.local/share/bash-completion/completions'
            comp.mkdir(parents=True)
            (comp / 'gh').write_text('# owner file\n')
            env = {'HOME': str(home), 'PATH': f'{fake}:/usr/bin:/bin'}
            result = subprocess.run(['bash', str(SRC / 'completions.sh')], capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('__start_kubectl k', (comp / 'k').read_text())
            self.assertTrue((comp / 'kubectl').exists())
            self.assertFalse((comp / 'helm').exists())
            self.assertEqual((comp / 'gh').read_text(), '# owner file\n')
            self.assertEqual([p.name for p in comp.glob('.*')], [])


class DevDiskReclaimTests(unittest.TestCase):
    def test_default_is_report_only_without_sudo_branch(self):
        script = (SRC / 'dev-disk-reclaim').read_text()
        self.assertNotIn('sudo -n', script)
        self.assertNotIn('autoremove', script)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / '.cache/clone/target'
            target.mkdir(parents=True)
            (target / '.rustc_info.json').write_text('{}')
            (target / 'CACHEDIR.TAG').write_text('Signature: 8a477f597d28d172789f06886806bc55')
            os.utime(target / '.rustc_info.json', (0, 0))
            os.utime(target / 'CACHEDIR.TAG', (0, 0))
            os.utime(target, (0, 0))
            env = {'HOME': tmp, 'USER': 'nobody-test', 'XDG_RUNTIME_DIR': tmp, 'PATH': '/usr/bin:/bin'}
            result = subprocess.run(['bash', str(SRC / 'dev-disk-reclaim')], capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('mode=DRY-RUN', result.stdout)
            self.assertIn(str(target), result.stdout)
            self.assertTrue(target.exists())


class ConfigTests(unittest.TestCase):
    def test_mount_validation(self):
        shell_tools.validate_mounts({'onedrive': 'OneDrive'})
        for bad in ({'a;b': 'X'}, {'a': '../x'}, {'a': 'x/y'}, {'a': '%h'}):
            with self.assertRaises(ValueError):
                shell_tools.validate_mounts(bad)
        self.assertEqual(shell_tools.RCLONE_MOUNTS, {})

    def test_pins_are_exact(self):
        self.assertRegex(shell_tools.NVIM_SIMPLE_COMMIT, r'^[0-9a-f]{40}$')
        for commit in shell_tools.NVIM_PLUGINS.values():
            self.assertRegex(commit, r'^[0-9a-f]{40}$')
        for version in shell_tools.NPM_TOOLS.values():
            self.assertRegex(version, r'^\d+\.\d+\.\d+$')

    def test_loader_and_scripts_parse(self):
        for name in ('grml.bash', 'history.bash', 'completions.sh', 'nvim-simple.sh', 'dev-disk-reclaim'):
            subprocess.run(['bash', '-n', str(SRC / name)], check=True)
        subprocess.run(['bash', '-n', '-c', shell_tools.BASH_INIT], check=True)
        self.assertNotIn('COPILOT_GITHUB_TOKEN', (SRC / 'grml.bash').read_text())


if __name__ == '__main__':
    unittest.main()


class BleshMarkerTests(unittest.TestCase):
    def test_block_markers_have_no_regex_metacharacters(self):
        # pyinfra's files.block matches markers as regular expressions: "(...)" never matched
        # its own block and duplicated it on every run.
        from manage import shell_tools as st
        for marker in (st.BLESH_TOP_MARKER, st.BLESH_END_MARKER, st.BASH_MARKER, st.INPUTRC_MARKER):
            self.assertNotRegex(marker, r"[()\[\]*+?|^$\\]", marker)


class FishShellTests(unittest.TestCase):
    def test_every_grml_alias_has_a_fish_version(self):
        from manage import fish_shell as fs
        aliases = fs.grml_aliases((Path(__file__).resolve().parents[1] / "files/shell/grml.bash").read_text())
        self.assertTrue({"l", "ll", "..", "kbus", "dl"} <= aliases)
        self.assertEqual(aliases - set(fs.ABBR) - set(fs.WRAP) - fs.NATIVE, set())

    def test_fish_conf_ports_functions_and_safe_chain(self):
        from manage import fish_shell as fs
        from manage.shell_tools import SAFE_CHAIN_WRAPPED
        text = fs.fish_conf(SAFE_CHAIN_WRAPPED)
        for fn in ("mkcd", "cdt", "bk", "sll", "ssearch", "cd", "fish_prompt", "dpkg-buildpackage", "debuild", "nvm"):
            self.assertRegex(text, rf"\nfunction {re.escape(fn)}( |\n)")
        for tool in SAFE_CHAIN_WRAPPED:
            self.assertIn(f"alias {tool} aikido-{tool}", text)
        self.assertNotIn("aikido", fs.fish_conf(()))

    def test_bash_hands_over_only_interactively(self):
        from manage import fish_shell as fs
        for guard in ("$- == *i*", "BASH_EXECUTION_STRING", "-t 0", "T2_NO_FISH", '!= fish', "PROMPT_COMMAND"):
            self.assertIn(guard, fs.BASHRC)


class FishExtrasTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_palettes_cover_all_five_and_pick_readable_sets(self):
        from manage import fish_shell as fs
        for t in ("cobalt", "navy", "fixedsys", "cream", "petrol"):
            text = fs.palette_theme((self.ROOT / f"files/themes/foot/themes/{t}.ini").read_text(), t)
            self.assertRegex(text, r"set -U fish_color_command [0-9a-f]{6} --bold\n")
            self.assertIn("set -U t2_color_git ", text)
        cream = fs.palette_theme((self.ROOT / "files/themes/foot/themes/cream.ini").read_text(), "cream")
        self.assertIn("fish_color_command 8a6a20", cream)        # regular yellow on the light background
        cobalt = fs.palette_theme((self.ROOT / "files/themes/foot/themes/cobalt.ini").read_text(), "cobalt")
        self.assertIn("fish_color_command ffe9a8", cobalt)       # bright yellow on the dark one

    def test_bash_history_to_fish(self):
        from manage import fish_shell as fs
        text = "#1700000000\nls -l\n#1700000005\nfor x in a; do\n  echo \\$x\ndone\n#1700000009\nls -l\n"
        out = fs.bash_history_to_fish(text, 1)
        self.assertEqual(out, "- cmd: for x in a; do\\n  echo \\\\$x\\ndone\n  when: 1700000005\n"
                              "- cmd: ls -l\n  when: 1700000009\n")
        self.assertEqual(fs.bash_history_to_fish("git status\n\npwd\n", 7),
                         "- cmd: git status\n  when: 7\n- cmd: pwd\n  when: 7\n")

    def test_fish_conf_has_the_extras(self):
        from manage import fish_shell as fs
        text = fs.fish_conf(())
        for needle in ("fzf --fish | source", "--on-event fish_postexec", "function fish_right_prompt",
                       "set -q t2_color_git; or set -g t2_color_git",
                       "abbr --add !! --position anywhere --function __t2_last_history_item",  # sudo !!
                       "path basename -- $cmd",
                       "shell-integration/fish/vendor_conf.d/ghostty-shell-integration.fish"):  # ssh terminfo                                              # title = program
            self.assertIn(needle, text)

    def test_termtheme_switches_fish(self):
        text = (self.ROOT / "files/themes/bin/hypr-termtheme").read_text()
        self.assertIn('("fish", t_fish)', text)
        self.assertNotIn('"--no-config"', text)   # that mode never saves universal variables


class StarshipTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def conf(self, current="navy"):
        from manage import starship as st
        return st.config({t: (self.ROOT / f"files/themes/foot/themes/{t}.ini").read_text() for t in st.THEMES}, current)

    def test_config_has_all_palettes_and_roles(self):
        import tomllib
        from manage import starship as st
        data = tomllib.loads(self.conf())
        self.assertEqual(data["palette"], "navy")
        self.assertEqual(set(data["palettes"]), set(st.THEMES))
        for pal in data["palettes"].values():
            self.assertEqual(set(pal), {"fg", "dim", "err", "user", "git", "lang"})
        for m in st.LANGS:
            self.assertIn(f"${m}", data["format"])
            self.assertIn(m, data)

    def test_switch_palette_changes_one_line(self):
        from manage import starship as st
        text = self.conf("cobalt")
        new = st.switch_palette(text, "cream")
        self.assertIn('palette = "cream"', new)
        self.assertEqual(len(new.splitlines()), len(text.splitlines()))
        self.assertEqual(self.conf("unknown").count('palette = "cobalt"'), 1)

    def test_bash_and_fish_hooks(self):
        from manage import fish_shell as fs, starship as st
        self.assertIn('eval "$(starship init bash)"', st.BASHRC)
        self.assertIn("__grml_prompt() { return $?; }", st.BASHRC)
        self.assertIn("starship init fish | source", fs.fish_conf((), True))
        self.assertNotIn("starship", fs.fish_conf((), False))
        self.assertIn('("starship", t_starship)', (self.ROOT / "files/themes/bin/hypr-termtheme").read_text())
