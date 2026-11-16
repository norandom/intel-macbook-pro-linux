"""Disposable-root service policy and locking transactions."""
import fcntl
import multiprocessing
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

from manage import package_transaction as tx
from manage import packages as guard


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for directory in ('usr/sbin', 'var/lib/dpkg', 'var/lib/t2-mac-kde', 'run/lock'):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
            (self.root / directory).chmod(0o755)
        for name in ('lock', 'lock-frontend'):
            (self.root / 'var/lib/dpkg' / name).touch()
        self.policy = self.root / 'usr/sbin/policy-rc.d'
        self.receipt = self.root / 'var/lib/t2-mac-kde/service-start-policy.json'

    def test_absent_policy_published_with_receipt_and_removed_on_success_and_failure(self):
        for fail in (False, True):
            with self.subTest(fail=fail):
                try:
                    with tx.package_transaction(prevent_service_start=True, root=self.root):
                        self.assertEqual(self.policy.read_bytes(), tx.DENY_ALL)
                        self.assertTrue(self.receipt.exists())
                        self.assertEqual(self.receipt.stat().st_mode & 0o777, 0o600)
                        if fail:
                            raise ValueError('install failed')
                except ValueError:
                    pass
                self.assertFalse(self.policy.exists())
                self.assertFalse(self.receipt.exists())

    def test_known_deny_all_is_reused_byte_for_byte_and_inode_unchanged(self):
        self.policy.write_bytes(tx.DENY_ALL)
        self.policy.chmod(0o755)
        original = self.policy.stat()
        with tx.package_transaction(prevent_service_start=True, root=self.root):
            self.assertFalse(self.receipt.exists())
        self.assertEqual(self.policy.stat(), original)
        self.assertEqual(self.policy.read_bytes(), tx.DENY_ALL)

    def test_foreign_symlink_and_unsafe_policy_block_unchanged(self):
        for content, mode in ((b'#!/bin/sh\nexit 0\n', 0o755), (tx.DENY_ALL, 0o777)):
            self.policy.write_bytes(content)
            self.policy.chmod(mode)
            with self.assertRaises(RuntimeError):
                with tx.package_transaction(prevent_service_start=True, root=self.root):
                    self.fail('must not enter install')
            self.assertEqual(self.policy.read_bytes(), content)
            self.assertFalse(self.receipt.exists())
        self.policy.unlink()
        self.policy.symlink_to('/bin/true')
        with self.assertRaises(RuntimeError):
            tx.inspect_service_policy(root=self.root)
        self.assertTrue(self.policy.is_symlink())

    def test_preview_no_files_written(self):
        before = list(self.root.rglob('*'))
        tx.inspect_service_policy(root=self.root)
        self.assertEqual(before, list(self.root.rglob('*')))

    def test_interrupted_owned_policy_recovers_before_default_transaction(self):
        tx._publish(self.root)
        self.assertTrue(self.policy.exists())
        with tx.package_transaction(root=self.root):
            self.assertFalse(self.policy.exists())
            self.assertFalse(self.receipt.exists())

    def test_process_death_leaves_receipt_and_next_transaction_recovers(self):
        def crash(root):
            with tx.package_transaction(prevent_service_start=True, root=root):
                os._exit(23)
        child = multiprocessing.get_context('fork').Process(target=crash, args=(self.root,))
        child.start()
        child.join(5)
        self.assertEqual(child.exitcode, 23)
        self.assertTrue(self.policy.exists())
        self.assertTrue(self.receipt.exists())
        with tx.package_transaction(root=self.root):
            self.assertFalse(self.policy.exists())
            self.assertFalse(self.receipt.exists())

    def test_apt_failure_runs_under_suppression_then_restores_policy(self):
        transaction = tx.package_transaction
        def apt(*args, **kwargs):
            self.assertEqual(self.policy.read_bytes(), tx.DENY_ALL)
            raise subprocess.CalledProcessError(100, args[0])
        with patch.object(guard.os, 'geteuid', return_value=0), \
             patch.object(guard, 'validate_request'), \
             patch('manage.package_policy.verify_effective_policy'), \
             patch.object(guard, 'inspect_plan', return_value=guard.PackagePlan((('btop', '1'),), ())), \
             patch.object(tx, 'package_transaction', side_effect=lambda **kw: transaction(root=self.root, **kw)), \
             patch.object(guard.subprocess, 'run', side_effect=apt):
            with self.assertRaises(subprocess.CalledProcessError):
                guard._apply_install(guard.PackageRequest(('btop',), 'ubuntu'), prevent_service_start=True)
        self.assertFalse(self.policy.exists())
        self.assertFalse(self.receipt.exists())

    def test_foreign_edit_or_replacement_during_install_is_restoration_conflict(self):
        for replacement in (False, True):
            with self.subTest(replacement=replacement):
                if self.policy.exists():
                    self.policy.unlink()
                if self.receipt.exists():
                    self.receipt.unlink()
                with self.assertRaisesRegex(RuntimeError, 'conflict'):
                    with tx.package_transaction(prevent_service_start=True, root=self.root):
                        if replacement:
                            self.policy.unlink()
                            self.policy.write_bytes(tx.DENY_ALL)
                            self.policy.chmod(0o755)
                        else:
                            self.policy.write_bytes(b'foreign edited policy')
                self.assertTrue(self.policy.exists())
                self.assertTrue(self.receipt.exists())

    def test_managed_lock_serializes_default_and_suppressed_requests(self):
        with tx.package_transaction(root=self.root):
            for suppressed in (False, True):
                with self.assertRaisesRegex(RuntimeError, 'concurrent'):
                    with tx.package_transaction(prevent_service_start=suppressed, root=self.root):
                        self.fail('concurrent install admitted')
        self.assertFalse(self.policy.exists())

    def test_native_locks_block_without_staging_policy(self):
        for name in ('lock', 'lock-frontend'):
            ready, release = multiprocessing.get_context('fork').Pipe()
            def hold(connection, path):
                with open(path, 'r+') as file:
                    fcntl.lockf(file, fcntl.LOCK_EX)
                    connection.send('locked')
                    connection.recv()
            child = multiprocessing.get_context('fork').Process(target=hold, args=(release, self.root / 'var/lib/dpkg' / name))
            child.start()
            ready.recv()
            try:
                with self.assertRaisesRegex(RuntimeError, 'package-manager'):
                    with tx.package_transaction(prevent_service_start=True, root=self.root, lock_timeout=0):
                        self.fail('native lock ignored')
                self.assertFalse(self.policy.exists())
                self.assertFalse(self.receipt.exists())
            finally:
                ready.send('done')
                child.join(5)
                if child.is_alive():
                    child.kill()
