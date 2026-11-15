import os
import shutil
import subprocess
import tempfile
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
