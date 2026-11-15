"""Speaker DSP: speakers only, per-user paths, revertable (no system WirePlumber files)."""
import json
from pathlib import Path
import unittest

from manage import speaker_dsp as sd

ROOT = Path(__file__).resolve().parents[1]


class SpeakerDspTests(unittest.TestCase):
    def test_graph_points_at_the_user_copy_and_all_firs_exist(self):
        user = "/home/u/.local/share/t2-mac-kde/speaker-dsp/16_1"
        text = sd.graph((ROOT / "files/speaker-dsp/16_1/graph.json").read_text(), user)
        self.assertNotIn("/usr/share", text)
        for path in {p for p in json.dumps(json.loads(text)).split('"') if p.endswith(".wav")}:
            self.assertTrue((ROOT / "files/speaker-dsp/16_1" / Path(path).name).is_file(), path)

    def test_dropin_is_speakers_only(self):
        conf = sd.wireplumber_conf("/x/graph.json")
        self.assertIn("HiFi__Speaker__sink", conf)
        self.assertNotIn("Mic", conf)
        self.assertNotIn("mic.json", conf)
        lua = (ROOT / "files/speaker-dsp" / sd.SCRIPT).read_text()
        self.assertNotIn("BuiltinMic", lua)
        self.assertNotIn('Pod.Array({ "Spa:Float", 1.0 })', lua)   # one value = front-left only

    def test_dsp_attaches_to_the_split_speaker_sink(self):
        conf = sd.wireplumber_conf("/x/graph.json")
        self.assertIn(sd.SPEAKER_SINK, conf)
        self.assertNotIn("monitor.alsa.rules", conf)
        text = sd.graph((ROOT / "files/speaker-dsp/16_1/graph.json").read_text(), "/u")
        self.assertEqual(json.loads(text)["playback.props"]["target.object"], sd.SPEAKER_SINK)

    def test_licence_is_shipped(self):
        self.assertIn("MIT", (ROOT / "files/speaker-dsp/COPYRIGHT").read_text())


if __name__ == "__main__":
    unittest.main()
