"""Static checks for the Hyprland desktop port (tasks/desktop.py, files/desktop, templates/desktop)."""
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jinja2

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "files/desktop"
TPL = ROOT / "templates/desktop"


def load_script(name):
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(SRC / "bin" / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    old, sys.dont_write_bytecode = sys.dont_write_bytecode, True   # no __pycache__ in files/
    try:
        loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = old
    return mod


hw = load_script("hypr-windows")

# hyprbars 0.53.0 option names (strings of the packaged libhyprbars.so)
HYPRBARS_KEYS = {"bar_blur", "bar_button_padding", "bar_buttons_alignment", "bar_color", "bar_height",
                 "bar_padding", "bar_part_of_window", "bar_precedence_over_border", "bar_text_align",
                 "bar_text_font", "bar_text_size", "bar_title_enabled", "col.text", "enabled",
                 "hyprbars-button", "icon_on_hover", "inactive_button_color", "on_double_click"}
DISPATCHERS = {"exec", "killactive", "fullscreen", "togglefloating", "movefocus", "cyclenext",
               "bringactivetotop", "resizeactive", "togglespecialworkspace", "submap", "movewindow",
               "resizewindow"}


def mon(**kw):
    m = {"id": 0, "name": "eDP-1", "x": 0, "y": 0, "width": 2880, "height": 1800, "scale": 2.0,
         "transform": 0, "reserved": [0, 26, 0, 0], "activeWorkspace": {"id": 1}, "specialWorkspace": {"id": 0}}
    m.update(kw)
    return m


def win(addr="0x1", cls="foo", at=(100, 100), size=(400, 300), **kw):
    w = {"address": addr, "class": cls, "at": list(at), "size": list(size), "floating": True, "mapped": True,
         "hidden": False, "fullscreen": 0, "monitor": 0, "workspace": {"id": 1}, "pinned": False}
    w.update(kw)
    return w


class Geometry(unittest.TestCase):
    def test_logical_monitor_box(self):
        self.assertEqual(hw.mon_box(mon()), (0.0, 0.0, 1440.0, 900.0))
        self.assertEqual(hw.mon_box(mon(transform=1))[2:], (900.0, 1440.0))
        self.assertEqual(hw.mon_box(mon(scale=0))[2:], (2880.0, 1800.0))

    def test_geometry_file_roundtrip_and_validation(self):
        g = {"kitty": (0.1, 0.2, 0.5, 0.5)}
        self.assertEqual(hw.parse_geometry(hw.format_geometry(g)), g)
        bad = "x nan 0 1 1\ny 0 0 0 1\nz 0 0 1\nok 0 0 1 1\n"
        self.assertEqual(list(hw.parse_geometry(bad)), ["ok"])

    def test_placement_below_bar_and_cascade(self):
        m = mon()
        x, y, w, h = hw.placement((0.0, 0.0, 0.5, 0.5), m, "mac", [], "foo")
        self.assertEqual((x, y), (0, 26 + 24))
        other = win(at=(x, y))
        x2, y2, _, _ = hw.placement((0.0, 0.0, 0.5, 0.5), m, "mac", [other], "foo")
        self.assertEqual((x2, y2), (x + 32, y + 32))
        x3, _, _, _ = hw.placement((0.0, 0.0, 0.5, 0.5), m, "mac", [win(cls="bar", at=(x, y))], "foo")
        self.assertEqual(x3, x)

    def test_taskbar_minimize_events_target_only_the_requested_window(self):
        from unittest.mock import Mock
        worker = object.__new__(hw.Worker)
        worker.ipc = Mock()
        worker.unminimize = Mock()
        worker.handle("minimized>>ab,1")
        worker.ipc.batch.assert_called_once_with([
            "movetoworkspacesilent special:minimized,address:0xab"])
        worker.handle("minimized>>ab,0")
        worker.unminimize.assert_called_once_with("0xab")
        worker.ipc.reset_mock()
        worker.unminimize.reset_mock()
        for event in ("minimized>>ab,2", "minimized>>ab", "minimized>>ab;exec evil,1"):
            worker.handle(event)
        worker.ipc.batch.assert_not_called()
        worker.unminimize.assert_not_called()

    def test_minimized_picker_restores_by_index_and_cancel_does_nothing(self):
        from unittest.mock import Mock, patch
        windows = [{"address": "0xab", "class": "term", "title": "same", "monitor": 0,
                    "workspace": {"name": "special:minimized"}},
                   {"address": "0xcd", "class": "term", "title": "same", "monitor": 0,
                    "workspace": {"name": "special:minimized"}}]
        mons = [{"id": 0, "activeWorkspace": {"id": 1}, "specialWorkspace": {"name": ""}}]
        for code, output, expected in ((0, "1", True), (1, "", False), (0, "-1", False), (0, "bad", False)):
            ipc = Mock()
            ipc.query.side_effect = lambda kind: windows if kind == "clients" else mons
            with patch.object(hw.subprocess, "run", return_value=Mock(returncode=code, stdout=output)):
                hw.pick_minimized(ipc)
            if expected:
                ipc.batch.assert_called_once_with(hw.restore_cmds(windows[1], mons))
                self.assertNotIn("togglespecialworkspace minimized", ipc.batch.call_args.args[0])
            else:
                ipc.batch.assert_not_called()

    def test_minimized_window_restored_on_focus(self):
        mons = [{"id": 0, "focused": True, "activeWorkspace": {"id": 3},
                 "specialWorkspace": {"name": "special:minimized"}}]
        win = {"address": "0xab", "monitor": 0, "workspace": {"name": "special:minimized"}}
        self.assertEqual(hw.restore_cmds(win, mons), [
            "togglespecialworkspace minimized", "movetoworkspacesilent 3,address:0xab",
            "alterzorder top,address:0xab", "focuswindow address:0xab"])
        mons[0]["specialWorkspace"] = {"name": ""}          # overlay already closed: don't reopen it
        self.assertNotIn("togglespecialworkspace minimized", hw.restore_cmds(win, mons))
        self.assertEqual(hw.restore_cmds({**win, "workspace": {"name": "3"}}, mons), [])

    def test_snap_zones(self):
        m = mon()
        self.assertEqual(hw.snap_zone((0, 450), m), "left")
        self.assertEqual(hw.snap_zone((1439, 450), m), "right")
        self.assertEqual(hw.snap_zone((700, 0), m), "top")
        self.assertEqual(hw.snap_zone((0, 10), m), "top-left")
        self.assertEqual(hw.snap_zone((1439, 899), m), "bottom-right")
        self.assertIsNone(hw.snap_zone((700, 450), m))

    def test_snap_rect_uses_style_height_and_reserved_bar(self):
        m = mon()
        self.assertEqual(hw.snap_rect("left", m, "mac"), (2, 26 + 24 + 2, 720 - 4, 900 - 26 - 24 - 4))
        self.assertEqual(hw.snap_rect("top", m, "win311")[1], 26 + 22 + 2)
        x, y, w, h = hw.snap_rect("bottom-right", m, "mac")
        self.assertEqual((x, w), (722, 716))

    def test_desktop_context_hits(self):
        m = mon()
        clients = [win(at=(100, 100), size=(400, 300)), win(addr="0x2", at=(900, 500), workspace={"id": 5})]
        self.assertIsNone(hw.on_desktop((10, 10), [m], clients, "mac"))          # top bar
        self.assertIsNone(hw.on_desktop((200, 200), [m], clients, "mac"))        # window
        self.assertIsNone(hw.on_desktop((200, 80), [m], clients, "mac"))         # its title bar
        self.assertEqual(hw.on_desktop((950, 550), [m], clients, "mac"), (950, 550))  # other ws
        self.assertIsNone(hw.on_desktop((5000, 5000), [m], clients, "mac"))

    def test_geometry_cmds_reject_bad_address(self):
        self.assertEqual(hw.geometry_cmds("0x1;exec rm", 1, 2, 3, 4), [])
        self.assertEqual(hw.geometry_cmds("0xab", 1, 2, 3, 4),
                         ["resizewindowpixel exact 3 4,address:0xab", "movewindowpixel exact 1 2,address:0xab"])


class Config(unittest.TestCase):
    def render_bindings(self):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TPL)))
        return env.get_template("bindings.conf.j2").render()

    def test_bindings_mirrored_into_one_shot_submap(self):
        text = self.render_bindings()
        main, sub = text.split("submap = super", 1)
        sub = sub.split("submap = reset", 1)[0]
        supers = re.findall(r"^bindd = SUPER (\S*), ([^,]+), ([^,]+), (\w+)", main, re.M)
        self.assertGreater(len(supers), 20)
        for mods, key, desc, disp in supers:
            self.assertIn(f"bindd = {mods}, {key}, {desc}, {disp}", sub)
            self.assertIn(f"bind = {mods}, {key}, submap, reset", sub)
        used = set(re.findall(r"^bindd = [^,]*, [^,]+, [^,]+, (\w+)", text, re.M))
        used |= set(re.findall(r"^bindm?d? = [^,]*, mouse:\d+, [^,]+, (\w+)$", text, re.M))
        self.assertLessEqual(used, DISPATCHERS)
        self.assertIn("bindd = , catchall, Cancel one-shot Super, submap, reset", sub)
        self.assertIn("bindn = , mouse:273, exec, ~/.local/bin/hypr-windows context", text)

    def test_decorations_match_source(self):
        for style, height, buttons in (("mac", "24", 4), ("win311", "22", 4)):
            text = (SRC / f"hypr/decorations-{style}.conf").read_text()
            keys = set(re.findall(r"^\s+([\w.-]+) =", text, re.M))
            self.assertLessEqual(keys, HYPRBARS_KEYS, style)
            self.assertIn(f"bar_height = {height}", text)
            self.assertEqual(text.count("hyprbars-button ="), buttons)
            self.assertIn("bar_precedence_over_border = true", text)
            for line in re.findall(r"hyprbars-button = (.*)", text):
                self.assertEqual(len(line.split(",")), 5, line)
        self.assertIn("rgb($host_color) rgb(6b3d8a) rgb(2d7d82) rgb(9a8f3e) rgb(2e5a2e) rgb(151515) 45deg",
                      (SRC / "hypr/borders.conf").read_text())

    def test_keyboard_policy(self):
        text = (SRC / "hypr/input.conf").read_text()
        self.assertIn("kb_layout = de,us", text)
        self.assertIn("kb_variant = mac_nodeadkeys,", text)
        self.assertIn("kb_options = compose:caps,shift:both_capslock_cancel,altwin:swap_ralt_rwin,lv3:lalt_switch",
                      text)

    def test_no_vm_or_lua_leftovers(self):
        for p in list((SRC / "hypr").glob("*.conf")) + [TPL / "bindings.conf.j2", TPL / "waybar-config.jsonc.j2"]:
            text = p.read_text()
            for bad in ("hl.", "LP_NUM_THREADS", "llvmpipe", "hypr-rdp", "Virtual-1", "debian-hypr"):
                self.assertNotIn(bad, text, f"{p.name}: {bad}")

    def test_waybar_template_renders_json_both_branches(self):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TPL)))
        for graphs in (True, False):
            text = env.get_template("waybar-config.jsonc.j2").render(bar_graphs=graphs)
            text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
            cfg = json.loads(text)
            self.assertIn("custom/termtheme", cfg["modules-right"])
            self.assertEqual("custom/cpu" in cfg["modules-right"], graphs)
            self.assertNotIn("uwsm app", json.dumps(cfg))


class Scripts(unittest.TestCase):
    def run_state(self, home, *files):
        d = Path(home, ".config/hypr")
        d.mkdir(parents=True, exist_ok=True)
        for name, value in files:
            (d / name).write_text(value + "\n")
        env = dict(os.environ, HOME=home, PATH="/nonexistent:/usr/bin:/bin")
        env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        subprocess.run(["sh", str(SRC / "bin/hypr-desktop-state")], env=env, check=True)
        return (d / "state.conf").read_text()

    def test_state_renderer(self):
        with tempfile.TemporaryDirectory() as home:
            out = self.run_state(home, ("layout-mode", "golden-v"), ("decorations-style", "win311"),
                                 ("window-shadows", "on"))
            self.assertIn("layout-golden-v.conf", out)
            self.assertIn("shadow-win311.conf", out)
            self.assertIn("borders.conf", out)
            out = self.run_state(home, ("layout-mode", "bogus"), ("decorations-style", "x"), ("window-shadows", "off"))
            self.assertIn("layout-dynamic.conf", out)
            self.assertIn("shadow-off.conf", out)

    def test_saved_rabbit_filter_is_part_of_reloadable_config(self):
        with tempfile.TemporaryDirectory() as home:
            state = Path(home, ".local/state/hypr-nightmode")
            state.parent.mkdir(parents=True)
            for mode in ("green", "dark", "grayscale", "monochrome", "warmwhite"):
                state.write_text(mode + "\n")
                output = self.run_state(home)
                self.assertIn(f"decoration:screen_shader = {home}/.config/hypr/shaders/night-{mode}.glsl", output)
                self.assertEqual(self.run_state(home), output)
            for mode in ("off", "invalid/path"):
                state.write_text(mode + "\n")
                output = self.run_state(home)
                self.assertIn("decoration:screen_shader =\n", output)
                self.assertNotIn("night-invalid", output)

    def test_state_prefers_patched_hyprbars_only_for_installed_hyprland(self):
        r = subprocess.run(["dpkg-query", "-W", "-f=${Version}", "hyprland"], capture_output=True, text=True)
        if r.returncode or not r.stdout:
            self.skipTest("hyprland not installed")
        with tempfile.TemporaryDirectory() as home:
            own = Path(home, ".local/lib/t2-mac-kde/hyprbars")
            own.mkdir(parents=True)
            (own / "libhyprbars.so").write_bytes(b"")
            (own / "stamp").write_text(f"hyprland={r.stdout} patch=abc\n")
            self.assertIn(f"plugin = {own}/libhyprbars.so", self.run_state(home))
            (own / "stamp").write_text("hyprland=0.0.0-old patch=abc\n")
            self.assertNotIn(str(own), self.run_state(home))

    def test_wallet_check_restarts_kwalletd6_until_it_reads(self):
        import importlib.machinery, importlib.util
        from unittest import mock
        loader = importlib.machinery.SourceFileLoader("hwc", str(SRC / "bin/hypr-wallet-check"))
        mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("hwc", loader))
        loader.exec_module(mod)
        with mock.patch.object(mod, "probe", return_value=("Chrome Keys", "Chrome Safe Storage")), \
             mock.patch.object(mod, "kwalletd6_reads", side_effect=[False, True]), \
             mock.patch.object(mod.subprocess, "run") as run, mock.patch.object(mod.time, "sleep"):
            self.assertEqual(mod.main(), 0)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args[0][0][:2], ["pkill", "-x"])
        with mock.patch.object(mod, "probe", return_value=("f", "k")), \
             mock.patch.object(mod, "kwalletd6_reads", return_value=False), \
             mock.patch.object(mod.subprocess, "run") as run, mock.patch.object(mod.time, "sleep"):
            self.assertEqual(mod.main(), 1)
        self.assertEqual(run.call_count, 3)
        with mock.patch.object(mod, "probe", return_value=None):
            self.assertEqual(mod.main(), 0)
        unit = (SRC / "systemd/hypr-secret-service.service").read_text()
        self.assertIn("ExecStart=-%h/.local/bin/hypr-wallet-check", unit)

    def test_hyprbars_patch_wired(self):
        patch = (SRC / "hyprbars/hyprbars-0.53.0-t2-input.patch").read_text()
        self.assertIn("(m_pWindow != window || WINDOWATCURSOR)", patch)
        self.assertIn("-    if (m_pWindow.lock() != Desktop::focusState()->window())", patch)
        task = (ROOT / "tasks/desktop.py").read_text()
        self.assertIn("build-hyprbars", task)
        self.assertIn("\"libgles-dev\"", task)  # GLES3/gl32.h, not pulled in by hyprland-dev
        self.assertIn("hypr-desktop-state --reload", task)

    def test_session_status_requires_explicit_instance(self):
        env = dict(os.environ)
        env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        r = subprocess.run(["python3", str(SRC / "bin/hypr-session"), "status", "--json"], env=env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["state"], "unavailable")
        r = subprocess.run(["python3", str(SRC / "bin/hypr-session"), "status", "--instance", "nope", "--json"],
                           env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_launch_preserves_arguments(self):
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d, "hyprctl")
            fake.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > {d}/out\n')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=f"{d}:/usr/bin:/bin", HYPRLAND_INSTANCE_SIGNATURE="x")
            subprocess.run(["sh", str(SRC / "bin/hypr-launch"), "echo", "a b", "it's"], env=env, check=True)
            cmd = Path(d, "out").read_text().splitlines()[2]
            self.assertEqual(cmd, "uwsm app -- 'echo' 'a b' 'it'\\''s'")
            r = subprocess.run(["sh", str(SRC / "bin/hypr-launch"), "no-such-app-zz"], env=env)
            self.assertEqual(r.returncode, 127)

    def test_termtheme_status_reads_only_known_names(self):
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, HOME=home)
            run = lambda: json.loads(subprocess.run(["sh", str(SRC / "bin/hypr-termtheme-status")], env=env,
                                                    capture_output=True, text=True).stdout)
            self.assertEqual(run()["class"], "default")
            state = Path(home, ".local/state/terminator-profile")
            state.parent.mkdir(parents=True)
            state.write_text("petrol\n")
            self.assertEqual(run()["class"], "petrol")
            state.write_text("navy\ncream\n")
            self.assertEqual(run()["class"], "invalid")


class Boundaries(unittest.TestCase):
    def test_task_stays_inside_desktop_scope(self):
        text = (ROOT / "tasks/desktop.py").read_text().lower()
        for bad in ("snapd", "\"flatpak", "sddm.conf", "autologin=", "apt-get", "grub", "initramfs",
                    "wireplumber.conf", "enable --now"):
            self.assertFalse(bad in text, bad)
        self.assertIn("install_packages(packagerequest(", text)

    def test_units_not_wanted_by_every_graphical_login(self):
        for p in (SRC / "systemd").iterdir():
            self.assertNotIn("WantedBy=graphical-session.target", p.read_text(), p.name)
            self.assertNotIn("WantedBy=default.target", p.read_text(), p.name)


if __name__ == "__main__":
    unittest.main()


class BarIconTests(unittest.TestCase):
    """Nerd Font glyphs must survive editing (empty icon strings rendered as blank gaps)."""

    def test_battery_and_power_profile_icons_are_not_empty(self):
        import jinja2, json as _json, re as _re, subprocess as _sp
        root = Path(__file__).resolve().parents[1]
        text = jinja2.Template((root / "templates/desktop/waybar-config.jsonc.j2").read_text()).render(
            bar_graphs=False, left_reserve=0)
        cfg = _json.loads("\n".join(l for l in text.splitlines() if not l.strip().startswith("//")))
        self.assertTrue(all(cfg["battery"]["format-icons"]))
        script = (root / "files/desktop/bin/hypr-power-profile").read_text()
        self.assertNotIn('icon=""', script)
        menu = (root / "files/desktop/waybar/power-profile-menu.xml").read_text()
        self.assertEqual(len(_re.findall(r'label">\S+  ', menu)), 3)


class AppMenuLaunch(unittest.TestCase):
    """hypr-appmenu imports GTK at load time, so only its launch helper is compiled here."""

    def setUp(self):
        import ast
        tree = ast.parse((SRC / "bin/hypr-appmenu").read_text())
        keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == "launch_argv")
                or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "UWSM_ID")]
        self.ns = {"re": re, "shlex": __import__("shlex")}
        exec(compile(ast.Module(body=keep, type_ignores=[]), "hypr-appmenu", "exec"), self.ns)

    def test_valid_id_goes_to_uwsm_by_id(self):
        self.assertEqual(self.ns["launch_argv"]("vivaldi-stable.desktop", "/usr/bin/vivaldi-stable %U"),
                         ["uwsm", "app", "--", "vivaldi-stable.desktop"])

    def test_id_uwsm_refuses_starts_from_exec(self):
        # rclone-ui ships "Rclone UI.desktop"; uwsm: Invalid Desktop Entry ID
        self.assertEqual(self.ns["launch_argv"]("Rclone UI.desktop", '"Rclone UI"'),
                         ["uwsm", "app", "--", "Rclone UI"])
        self.assertEqual(self.ns["launch_argv"]("a b.desktop", "tool --x %U 100%%"),
                         ["uwsm", "app", "--", "tool", "--x", "100%"])


class XScale(unittest.TestCase):
    def setUp(self):
        loader = importlib.machinery.SourceFileLoader("hxs", str(SRC / "bin/hypr-xscale"))
        self.m = importlib.util.module_from_spec(importlib.util.spec_from_loader("hxs", loader))
        loader.exec_module(self.m)

    def test_dpi_follows_the_internal_panel(self):
        mons = [{"name": "hypr-rdp", "scale": 2.0}, {"name": "eDP-1", "scale": 1.6}]
        self.assertEqual(self.m.dpi_for(self.m.panel_scale(mons)), 154)
        self.assertEqual(self.m.dpi_for(self.m.panel_scale([])), 96)

    def test_resources_scale_core_fonts(self):
        res = self.m.resources(154)
        self.assertIn("Xft.dpi: 154\n", res)
        self.assertIn("courier-medium-r-normal--22-", res)   # NEdit 14 px x 1.6
        self.assertIn("x3270.emulatorFont: 12x24", res)
        self.assertIn("x3270.emulatorFont: 3270", self.m.resources(96))

    def test_xfe_screenres_set_in_settings_only(self):
        text = "[OPTIONS]\nscreenres=1\n\n[SETTINGS]\nbasecolor=Silver\nscreenres=96\n\n[FILETYPES]\nx=y\n"
        out = self.m.set_screenres(text, 154)
        self.assertEqual(out, "[OPTIONS]\nscreenres=1\n\n[SETTINGS]\nbasecolor=Silver\nscreenres=154\n\n[FILETYPES]\nx=y\n")
        self.assertEqual(self.m.set_screenres(out, 154), out)
        added = self.m.set_screenres("[SETTINGS]\nbasecolor=Silver\n\n[FILETYPES]\n", 154)
        self.assertIn("basecolor=Silver\nscreenres=154\n\n[FILETYPES]", added)
        self.assertEqual(self.m.set_screenres("", 120), "[SETTINGS]\nscreenres=120\n")


class NightShift(unittest.TestCase):
    def test_location_from_timezone_table(self):
        from manage import night_shift as ns
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("#comment\nDE,DK\t+5230+01322\tEurope/Berlin\tmost of Germany\n"
                    "US\t+404251-0740023\tAmerica/New_York\tEastern\n")
        self.assertEqual(ns.timezone_location("Europe/Berlin", (f.name,)), (52.5, 13.37))
        self.assertEqual(ns.timezone_location("America/New_York", (f.name,)), (40.71, -74.01))
        self.assertIsNone(ns.timezone_location("Mars/Base", (f.name,)))

    def test_explicit_location_and_config(self):
        from manage import night_shift as ns
        self.assertEqual(ns.location("48.14:11.58"), (48.14, 11.58))
        for bad in ("munich", "95:0", "1:2:3"):
            with self.assertRaises(ValueError):
                ns.location(bad)
        ini = ns.config_ini(48.14, 11.58, 6500, 4500)
        self.assertIn("Managed by t2-mac-kde (desktop)", ini)
        self.assertIn("location-provider=manual\n", ini)
        self.assertIn("adjustment-method=wayland\n", ini)
        self.assertIn("lat=48.14\nlon=11.58\n", ini)
        with self.assertRaises(ValueError):
            ns.config_ini(48.14, 11.58, 6500, 99)

    def test_bar_module_only_when_enabled(self):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TPL)))
        for on in (True, False):
            text = env.get_template("waybar-config.jsonc.j2").render(bar_graphs=False, night_shift=on)
            cfg = json.loads(re.sub(r"^\s*//.*$", "", text, flags=re.M))
            self.assertEqual("custom/nightshift" in cfg["modules-right"], on)
        unit = (SRC / "systemd/hypr-gammastep.service").read_text()
        self.assertIn("PartOf=hypr-desktop.target", unit)
        self.assertIn("WantedBy=hypr-desktop.target", unit)
