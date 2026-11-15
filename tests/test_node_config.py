import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from manage.node import BASH_INIT, BASH_MARKER, default_alias_matches, validate_node_config


class NodeConfigTests(unittest.TestCase):
    def test_real_bash_block_apply_repeat_backup_and_scoped_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bashrc = root / '.bashrc'
            original = 'export EXISTING_CUSTOMIZATION=preserved\n'
            bashrc.write_text(original)
            deploy = root / 'block.py'
            def run(present):
                deploy.write_text('from pyinfra.operations import files\n'
                                  f'files.block(path={str(bashrc)!r}, content={BASH_INIT!r}, '
                                  f'marker={BASH_MARKER!r}, backup=True, present={present!r})\n')
                result = subprocess.run([sys.executable, '-m', 'pyinfra', '@local', str(deploy), '-y'],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run(True)
            self.assertIn(original, bashrc.read_text())
            self.assertEqual(bashrc.read_text().count('# BEGIN t2-mac-kde developer tools'), 1)
            self.assertTrue(any(path.read_text() == original for path in root.glob('.bashrc.*')))
            before = bashrc.stat().st_mtime_ns
            run(True)
            self.assertEqual(before, bashrc.stat().st_mtime_ns)
            with bashrc.open('a') as stream:
                stream.write('export LATER_USER_CHANGE=preserved\n')
            run(False)
            self.assertIn(original, bashrc.read_text())
            self.assertIn('export LATER_USER_CHANGE=preserved', bashrc.read_text())
            self.assertNotIn('NVM_DIR', bashrc.read_text())

    def test_bash_initialization_is_additive_and_does_not_duplicate_path(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            nvm = home / '.nvm'
            nvm.mkdir()
            (nvm / 'nvm.sh').write_text('export T2_NVM_LOADED=yes\n')
            result = subprocess.run(['/bin/bash', '--noprofile', '--norc', '-c',
                                     BASH_INIT + '\n' + BASH_INIT + '\nprintf "%s\\n%s" "$PATH" "$T2_NVM_LOADED"'],
                                    env={'HOME': str(home), 'PATH': '/usr/bin:/bin'},
                                    text=True, capture_output=True, check=True)
            path, loaded = result.stdout.splitlines()
            self.assertEqual(path, str(home / '.local/bin') + ':/usr/bin:/bin')
            self.assertEqual(loaded, 'yes')

    def test_exact_version_only(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(validate_node_config('26.13.1', home, {}), '26.13.1')
            for version in ('node', 'lts/*', 'v26.13.1', '26', '26.13.1;id', '26.13.1\nother'):
                with self.subTest(version=version), self.assertRaises(ValueError):
                    validate_node_config(version, home, {})

    def test_user_config_preserved_and_secrets_not_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / '.npmrc'
            safe = '//registry.example/:_authToken=secret\nregistry=https://example.test\n'
            config.write_text(safe)
            validate_node_config('26.13.1', home, {})
            for key in ('prefix', 'globalconfig', 'PREFIX'):
                content = safe + f'{key}=/secret/location\n'
                config.write_text(content)
                with self.assertRaises(RuntimeError) as caught:
                    validate_node_config('26.13.1', home, {})
                self.assertNotIn('secret', str(caught.exception))
                self.assertIn(key.lower(), str(caught.exception))
                self.assertEqual(config.read_text(), content)

    def test_environment_overrides_and_redirected_config_block(self):
        with tempfile.TemporaryDirectory() as directory:
            for key in ('NPM_CONFIG_PREFIX', 'npm_config_prefix', 'PREFIX',
                        'NPM_CONFIG_GLOBALCONFIG', 'npm_config_userconfig', 'NVM_DIR'):
                with self.subTest(key=key), self.assertRaises(RuntimeError) as caught:
                    validate_node_config('26.13.1', Path(directory), {key: '/private/value'})
                self.assertNotIn('/private/value', str(caught.exception))

    def test_normal_nvm_dir_and_userconfig_are_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            validate_node_config('26.13.1', home, {
                'NVM_DIR': str(home / '.nvm'), 'NPM_CONFIG_USERCONFIG': str(home / '.npmrc')})

    def test_default_alias_must_be_exact_not_moving(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertFalse(default_alias_matches(home, '26.13.1'))
            alias = home / '.nvm/alias/default'
            alias.parent.mkdir(parents=True)
            for target, expected in [('node', False), ('lts/*', False), ('26.13.1\n', True),
                                     ('v26.13.1', False), ('26.13.0', False)]:
                alias.write_text(target)
                self.assertEqual(default_alias_matches(home, '26.13.1'), expected)
