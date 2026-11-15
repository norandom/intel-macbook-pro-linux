"""EasyEffects QC35 3D: presets, IR, pins, autoload names, Bose detection, WirePlumber drop-in (offline)."""
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

from manage import audio_effects as ae

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "files/audio-effects"
EQ_TEXT = (SRC / "autoeq" / ae.AUTOEQ_FILE).read_text()
TASK = (ROOT / "tasks/audio_effects.py").read_text()
MAC = "60:AB:D2:00:00:01"


def _tool():
    spec = importlib.util.spec_from_file_location("make_hrir", ROOT / "tools/make_hrir.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class PinTests(unittest.TestCase):
    def test_pins_are_well_formed_and_match_committed_files(self):
        self.assertRegex(ae.AUTOEQ_COMMIT, r"\A[0-9a-f]{40}\Z")
        for sha in (ae.AUTOEQ_SHA256, ae.IR_SHA256, _tool().HRTF_SHA256):
            self.assertRegex(sha, r"\A[0-9a-f]{64}\Z")
        self.assertEqual(hashlib.sha256((SRC / "autoeq" / ae.AUTOEQ_FILE).read_bytes()).hexdigest(), ae.AUTOEQ_SHA256)
        self.assertEqual(hashlib.sha256((SRC / "irs" / f"{ae.IR_NAME}.irs").read_bytes()).hexdigest(), ae.IR_SHA256)
        self.assertIn(ae.AUTOEQ_COMMIT, (SRC / "autoeq/SOURCE.txt").read_text())
        self.assertIn("MIT License", (SRC / "autoeq/LICENSE").read_text())
        credits = (SRC / "irs/CREDITS.txt").read_text()
        self.assertIn("Gardner", credits)
        self.assertIn(_tool().HRTF_SHA256, credits)
        self.assertTrue(_tool().HRTF_URL.startswith("https://sound.media.mit.edu/"))

    def test_task_checks_pins_and_uses_the_guarded_installer(self):
        self.assertIn("install_packages(PackageRequest(packages=ae.PACKAGES", TASK)
        self.assertNotRegex(TASK, r"apt(-get)? install|_sudo=True|/etc/|/usr/share/(wireplumber|pipewire|alsa)")
        self.assertEqual(set(ae.PACKAGES), {"easyeffects", "lsp-plugins-lv2", "calf-plugins"})


class IrTests(unittest.TestCase):
    def test_ir_is_four_channel_48k_wav(self):
        with wave.open(str(SRC / "irs" / f"{ae.IR_NAME}.irs")) as w:
            self.assertEqual((w.getnchannels(), w.getframerate(), w.getsampwidth()), (4, 48000, 2))
            self.assertGreater(w.getnframes(), 128)
            frames = w.readframes(w.getnframes())
        import struct
        s = struct.unpack(f"<{len(frames) // 2}h", frames)
        energy = [sum(x * x for x in s[c::4]) for c in range(4)]
        self.assertEqual(energy[0], energy[3])          # LL == RR (symmetric set)
        self.assertEqual(energy[1], energy[2])          # LR == RL
        self.assertGreater(energy[0], energy[1])        # ipsilateral louder than contralateral

    def test_resampler_keeps_dc_gain(self):
        out = _tool().resample([1.0] * 400)
        mid = out[len(out) // 3: 2 * len(out) // 3]
        self.assertTrue(all(abs(v - 1.0) < 0.02 for v in mid))


class PresetTests(unittest.TestCase):
    def setUp(self):
        self.p = json.loads(ae.dumps(ae.preset_3d(EQ_TEXT)))["output"]

    def test_plugin_order(self):
        self.assertEqual(self.p["plugins_order"],
                         ["equalizer#0", "bass_enhancer#0", "crossfeed#0", "convolver#0", "limiter#0"])
        for name in self.p["plugins_order"]:
            self.assertIn(name, self.p)
        self.assertEqual(self.p["blocklist"], [])

    def test_equalizer_is_the_autoeq_result(self):
        preamp, filters = ae.parse_parametric_eq(EQ_TEXT)
        eq = self.p["equalizer#0"]
        self.assertEqual(eq["input-gain"], preamp)
        self.assertEqual(preamp, -4.3)
        self.assertEqual(eq["num-bands"], len(filters))
        self.assertEqual(eq["mode"], "IIR")
        self.assertEqual(eq["left"], eq["right"])
        self.assertEqual(eq["left"]["band0"], {"type": "Lo-shelf", "mode": "APO (DR)", "slope": "x1", "solo": False,
                                               "mute": False, "gain": -1.3, "frequency": 105.0, "q": 0.7,
                                               "width": 4.0})
        self.assertEqual(eq["left"]["band5"]["type"], "Hi-shelf")
        self.assertEqual({b["type"] for b in eq["left"].values()}, {"Bell", "Lo-shelf", "Hi-shelf"})

    def test_enhancer_crossfeed_convolver_limiter(self):
        self.assertTrue(0 < self.p["bass_enhancer#0"]["amount"] <= 6)
        self.assertEqual((self.p["crossfeed#0"]["fcut"], self.p["crossfeed#0"]["feed"]), (700, 4.5))
        conv = self.p["convolver#0"]
        self.assertEqual(conv["kernel-name"], ae.IR_NAME)
        self.assertEqual(conv["ir-width"], 100)
        wet, dry = 10 ** (conv["wet"] / 20), 10 ** (conv["dry"] / 20)
        self.assertAlmostEqual(wet, 0.85, delta=0.01)
        self.assertAlmostEqual(dry, 0.15, delta=0.01)
        lim = self.p["limiter#0"]
        self.assertEqual((lim["threshold"], lim["gain-boost"], lim["bypass"]), (-1.0, False, False))

    def test_bypass_preset_is_empty(self):
        self.assertEqual(ae.preset_bypass(), {"output": {"blocklist": [], "plugins_order": []}})

    def test_bad_autoeq_lines_are_rejected(self):
        with self.assertRaises(ValueError):
            ae.parse_parametric_eq("Preamp: -1 dB\nFilter 1: ON XX Fc 1 Hz Gain 1 dB Q 1\n")


class AutoloadTests(unittest.TestCase):
    def test_t2_sinks_get_bypass_for_both_card_routes(self):
        names = {n for n, _e in ae.t2_autoloads()}
        self.assertIn("alsa_output.pci-0000_04_00.3.HiFi__Speaker__sink:Internal Speakers.json", names)
        self.assertIn("alsa_output.pci-0000_04_00.3.HiFi__Headphones__sink:Headphones.json", names)
        self.assertEqual(len(names), 4)
        self.assertTrue(all(e["preset-name"] == "Bypass" for _n, e in ae.t2_autoloads()))
        self.assertIn(("Window", "outputAutoloadingFallbackPreset", "Bypass"), ae.DB_SETTINGS)

    def test_qc35_autoload_targets_the_visible_sink(self):
        name, entry = ae.autoload_entry(ae.bt_sink_node(MAC.lower()), "bla", ae.BT_ROUTE, ae.PRESET_3D)
        self.assertEqual(name, "bluez_output.60:AB:D2:00:00:01:Headphones.json")
        self.assertEqual(entry, {"device": "bluez_output.60:AB:D2:00:00:01", "device-description": "bla",
                                 "device-profile": "Headphones", "preset-name": "QC35 3D"})


class DetectionTests(unittest.TestCase):
    INFO = ("Device 60:AB:D2:00:00:01 (public)\n\tAlias: bla\n\tPaired: yes\n\tTrusted: no\n"
            "\tUUID: Audio Sink                (0000110b-0000-1000-8000-00805f9b34fb)\n")

    def test_bose_oui_with_audio_sink(self):
        devices = "Device 60:AB:D2:00:00:01 bla\nDevice AA:BB:CC:00:11:22 AirPods\n"
        info = {MAC: self.INFO, "AA:BB:CC:00:11:22": self.INFO}
        self.assertEqual(ae.bose_macs(devices, info.get), [(MAC, "bla", False)])
        self.assertEqual(ae.bose_macs(devices, info.get, "aa:bb:cc:00:11:22"), [("AA:BB:CC:00:11:22", "bla", False)])
        self.assertEqual(ae.bose_macs(devices, lambda m: "Alias: x\n"), [])  # no A2DP sink
        self.assertEqual(ae.bose_macs("", info.get), [])

    def test_ouis(self):
        self.assertIn("60:AB:D2", ae.BOSE_OUIS)
        self.assertTrue(all(re.fullmatch(r"[0-9A-F]{2}(:[0-9A-F]{2}){2}", o) for o in ae.BOSE_OUIS))


class KConfigTests(unittest.TestCase):
    def test_sets_keys_and_keeps_the_rest(self):
        text = "[Window]\nwidth=900\noutputAutoloadingUsesFallback=false\n\n[EffectsPipelines]\nbypass=true\n"
        out = ae.set_kconfig(text, ae.DB_SETTINGS)
        self.assertIn("width=900", out)
        self.assertIn("bypass=true", out)
        self.assertIn("outputAutoloadingUsesFallback=true", out)
        self.assertNotIn("outputAutoloadingUsesFallback=false", out)
        self.assertEqual(out.count("[Window]"), 1)
        self.assertEqual(ae.set_kconfig(out, ae.DB_SETTINGS), out)
        self.assertIn("[Window]\noutputAutoloadingUsesFallback=true", ae.set_kconfig("", ae.DB_SETTINGS))


class WirePlumberTests(unittest.TestCase):
    def test_rendered_conf(self):
        conf = ae.wireplumber_conf([MAC])
        self.assertIn('device.name = "bluez_card.60_AB_D2_00_00_01"', conf)
        self.assertIn("bluez5.auto-connect = [ a2dp_sink ]", conf)
        self.assertIn("custom.t2-bose-mic-never-default = optional", conf)
        self.assertNotIn("alsa", conf)
        self.assertEqual(conf.count("{"), conf.count("}"))
        self.assertEqual(conf.count("["), conf.count("]"))
        dump = shutil.which("spa-json-dump")
        if dump:
            with tempfile.NamedTemporaryFile("w", suffix=".conf") as f:
                f.write(conf)
                f.flush()
                parsed = json.loads(subprocess.run([dump, f.name], capture_output=True, text=True, check=True).stdout)
            rule = parsed["monitor.bluez.rules"][0]
            self.assertEqual(rule["matches"], [{"device.name": "bluez_card.60_AB_D2_00_00_01"}])
            self.assertEqual(rule["actions"]["update-props"]["bluez5.auto-connect"], ["a2dp_sink"])
            self.assertEqual(parsed["wireplumber.components"][0]["name"], ae.WP_SCRIPT)

    def test_rendered_hook(self):
        lua = ae.wireplumber_script([MAC])
        self.assertIn('"bluez_input.60:AB:D2:00:00:01", "bluez_input.60_AB_D2_00_00_01"', lua)
        self.assertIn('Constraint { "default-node.type", "=", "audio.source" }', lua)
        self.assertEqual(lua.count("{"), lua.count("}"))
        self.assertEqual(lua.count("("), lua.count(")"))


if __name__ == "__main__":
    unittest.main()
