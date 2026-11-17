import os
from pathlib import Path
import pty
import subprocess
import tempfile
import tomllib
import unittest

from manage import fish_shell
from manage.warpeer import startup_shell_config, font_config


class WarpeerTests(unittest.TestCase):
    def test_native_shell_preserves_preferences_and_is_idempotent(self):
        for original in ('[appearance]\nfont_size = 14\n',
                         '[session]\nstartup_shell_override = "bash" # old\nother = true\n[appearance]\nfont_size = 14\n'):
            changed = startup_shell_config(original, 'fish')
            parsed = tomllib.loads(changed)
            self.assertEqual(parsed['session']['startup_shell_override'], 'fish')
            self.assertEqual(parsed['appearance']['font_size'], 14)
            self.assertEqual(startup_shell_config(changed, 'fish'), changed)

    def test_font_applies_to_terminal_content_and_ui_preserving_other_settings(self):
        original = ('[appearance.text]\nfont_size = 16\nfont_name = "Hack"\n'
                    '[runbooks]\nfolders = ["~/Runbooks"]\n')
        changed = font_config(original)
        parsed = tomllib.loads(changed)
        for key in ("font_name", "ai_font_name", "ui_font_name"):
            self.assertEqual(parsed['appearance']['text'][key], 'Fixedsys Excelsior')
        self.assertEqual(parsed['appearance']['text']['font_size'], 16)
        self.assertEqual(parsed['runbooks']['folders'], ['~/Runbooks'])
        self.assertEqual(font_config(changed), changed)
        for family in ('Font "Quoted"', r'Font \ Name'):
            self.assertEqual(tomllib.loads(font_config(changed, family))['appearance']['text']['font_name'], family)

    @unittest.skipUnless(Path('/usr/bin/fish').exists(), 'fish required')
    def test_warp_does_not_replace_its_bootstrapped_bash(self):
        for terminal, handover in (('WarpTerminal', False), ('terminator', True)):
            with self.subTest(terminal=terminal), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = root / 'result'
                rc = root / 'bashrc'
                rc.write_text(fish_shell.BASHRC + f'\ndeclare -p PROMPT_COMMAND > {result} 2>/dev/null\nexit 0\n')
                master, slave = pty.openpty()
                env = dict(os.environ, TERM_PROGRAM=terminal, TERM='xterm-256color')
                env.pop('T2_NO_FISH', None)
                try:
                    subprocess.run(['/bin/bash', '--noprofile', '--rcfile', str(rc), '-i'],
                                   stdin=slave, stdout=slave, stderr=slave, env=env, timeout=5, check=True)
                    self.assertEqual('__t2_fish' in result.read_text(), handover)
                finally:
                    os.close(master)
                    os.close(slave)
