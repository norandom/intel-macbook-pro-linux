"""hypr-rdp control/config fixtures (no server, no session, no network)."""
import importlib.machinery
import importlib.util
import json
import os
import socket
import tempfile
import tomllib
import unittest
from pathlib import Path

import jinja2

ROOT = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader("hypr_rdp_control", str(ROOT / "files/rdp/hypr-rdp-control"))
spec = importlib.util.spec_from_loader(loader.name, loader)
ctl = importlib.util.module_from_spec(spec)
loader.exec_module(ctl)


def render(**overrides):
    values = dict(rdp_version="v0.1.8", bind="127.0.0.1:3389", rdp_user="me", password_file="/x",
                  fps=30, audio_mode="mirror", hook="/home/me/.local/bin/hypr-rdp-session")
    values.update(overrides)
    text = (ROOT / "templates/rdp/config.toml.j2").read_text()
    return jinja2.Template(text).render(**values)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.secret = self.dir / "password"
        self.secret.write_text("s3cret")
        self.secret.chmod(0o600)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, text):
        path = self.dir / "config.toml"
        path.write_text(text)
        return path

    def test_rendered_template_is_valid_and_safe(self):
        cfg = ctl.load_config(self.write(render(password_file=str(self.secret))))
        self.assertEqual(cfg["auth_mode"], "configured")
        self.assertEqual(cfg["audio_mode"], "mirror")
        self.assertEqual(cfg["keyboard_layout_policy"], "compositor")
        self.assertEqual(cfg["file_transfer_mode"], "off")
        self.assertNotIn("password", cfg)
        self.assertTrue(cfg["on_session_end"].endswith("hypr-rdp-session end"))

    def test_rejects_unsafe_configs(self):
        good = render(password_file=str(self.secret))
        for bad in (good.replace('audio_mode = "mirror"', 'audio_mode = "redirect"'),
                    good.replace('auth_mode = "configured"', 'auth_mode = "pam"'),
                    good.replace('username = "me"', 'username = ""'),
                    good + 'password = "inline"\n',
                    render(password_file=str(self.dir / "absent"))):
            with self.assertRaises(ctl.Fail) as caught:
                ctl.load_config(self.write(bad))
            self.assertEqual(caught.exception.code, 2)

    def test_rejects_group_readable_or_empty_password(self):
        path = self.write(render(password_file=str(self.secret)))
        self.secret.chmod(0o640)
        with self.assertRaises(ctl.Fail):
            ctl.load_config(path)
        self.secret.chmod(0o600)
        self.secret.write_text("")
        with self.assertRaises(ctl.Fail):
            ctl.load_config(path)

    def test_error_never_prints_secret(self):
        path = self.write(render(password_file=str(self.secret)) + 'password = "s3cret"\n')
        with self.assertRaises(ctl.Fail) as caught:
            ctl.load_config(path)
        self.assertNotIn("s3cret", caught.exception.reason)

    def test_loopback(self):
        for bind in ("127.0.0.1:3389", "[::1]:3389", "localhost:3389"):
            self.assertTrue(ctl.is_loopback(bind), bind)
        for bind in ("0.0.0.0:3389", "192.168.1.5:3389", "[::]:3389"):
            self.assertFalse(ctl.is_loopback(bind), bind)


def status(**overrides):
    data = dict(schema_version=1, uid=os.getuid(), instance_signature="abc", compositor_version="0.53.3",
                wayland_display="wayland-1", runtime_dir="/run/user/1", state="ready")
    data.update(overrides)
    return lambda sig: (0, json.dumps(data))


class SessionTests(unittest.TestCase):
    env = {"HYPRLAND_INSTANCE_SIGNATURE": "abc"}

    def test_requires_explicit_instance(self):
        with self.assertRaises(ctl.Fail) as caught:
            ctl.select_session({"XDG_CURRENT_DESKTOP": "KDE"}, status())
        self.assertEqual(caught.exception.code, 2)

    def test_accepts_ready_own_session(self):
        self.assertEqual(ctl.select_session(self.env, status())["wayland_display"], "wayland-1")

    def test_rejects_wrong_user_stale_or_mismatch(self):
        for runner in (status(uid=os.getuid() + 1), status(state="stopping"), status(instance_signature="xyz"),
                       status(schema_version=2), lambda sig: (2, "")):
            with self.assertRaises(ctl.Fail):
                ctl.select_session(self.env, runner)

    def test_fallback_requires_live_own_socket(self):
        with tempfile.TemporaryDirectory() as runtime:
            env = {"HYPRLAND_INSTANCE_SIGNATURE": "abc", "XDG_RUNTIME_DIR": runtime, "WAYLAND_DISPLAY": "wayland-1"}
            orig = ctl._hypr_session
            ctl._hypr_session = lambda: None
            try:
                with self.assertRaises(ctl.Fail):
                    ctl.select_session(env)
                Path(runtime, "hypr/abc").mkdir(parents=True)
                sock = socket.socket(socket.AF_UNIX)
                sock.bind(str(Path(runtime, "hypr/abc/.socket.sock")))
                Path(runtime, "wayland-1").touch()
                self.assertEqual(ctl.select_session(env)["instance_signature"], "abc")
                sock.close()
            finally:
                ctl._hypr_session = orig

    def test_server_env_drops_software_rendering(self):
        env = ctl.server_env({"wayland_display": "w", "instance_signature": "s", "runtime_dir": "/r"},
                             {"LIBGL_ALWAYS_SOFTWARE": "1", "PATH": "/usr/bin"})
        self.assertNotIn("LIBGL_ALWAYS_SOFTWARE", env)
        self.assertEqual(env["HYPRLAND_INSTANCE_SIGNATURE"], "s")


class GateTests(unittest.TestCase):
    def test_unverified_lan_bind_warns_but_starts(self):
        import contextlib, io
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp, "hypr-rdp")
            binary.write_bytes(b"\x7fELF")
            marker = Path(tmp, "marker")
            session = {"compositor_version": "0.53.3"}
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                ctl.check_gate({"bind": "0.0.0.0:3389"}, session, marker, binary)
            self.assertIn("warning", err.getvalue())
            marker.write_text(ctl.evidence_key(session, binary))
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                ctl.check_gate({"bind": "0.0.0.0:3389"}, session, marker, binary)
            self.assertEqual(err.getvalue(), "")


class UnitTests(unittest.TestCase):
    def test_unit_starts_only_with_the_hyprland_session(self):
        lines = (ROOT / "files/rdp/t2-hypr-rdp.service").read_text().splitlines()
        text = "\n".join(line for line in lines if not line.startswith("#"))
        for line in ("Requisite=hypr-desktop.target", "PartOf=hypr-desktop.target",
                     "WantedBy=hypr-desktop.target", "ConditionEnvironment=HYPRLAND_INSTANCE_SIGNATURE"):
            self.assertIn(line, text)
        self.assertNotIn("graphical-session", text)
        self.assertNotIn("default.target", text)

    def test_run_waits_for_preparing_session(self):
        calls = []

        def select():
            calls.append(1)
            if len(calls) < 3:
                raise ctl.Fail(2, "preparing")
            return {"state": "ready"}
        self.assertEqual(ctl.wait_for_session(5, 0, select, lambda d: None)["state"], "ready")
        with self.assertRaises(ctl.Fail):
            ctl.wait_for_session(2, 0, lambda: (_ for _ in ()).throw(ctl.Fail(2, "x")), lambda d: None)

    def test_hook_does_not_touch_local_devices(self):
        text = (ROOT / "files/rdp/hypr-rdp-session").read_text()
        for forbidden in ("hyprctl", "pkill", "hyprlock", "wpctl", "pactl", "dpms"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
