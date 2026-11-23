import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from manage import kwin_rabbit

ROOT = Path(__file__).resolve().parents[1]
SHADERS = ROOT / "files/desktop/hypr/shaders"
MARKER = "Managed by t2-mac-kde (desktop)"


class KWinShaderTests(unittest.TestCase):
    def shader(self, mode):
        return kwin_rabbit.kwin_shader((SHADERS / f"night-{mode}.glsl").read_text(), MARKER)

    def test_every_hyprland_filter_has_a_kwin_variant(self):
        self.assertEqual(sorted(kwin_rabbit.MODES),
                         sorted(p.stem.removeprefix("night-") for p in SHADERS.glob("night-*.glsl")))
        for mode in kwin_rabbit.MODES:
            src = self.shader(mode)
            self.assertNotIn("#version", src)                      # the effect adds KWin's
            self.assertIn(MARKER, src)
            self.assertNotRegex(src, r"\btex\b|v_texcoord")       # KWin's names only
            self.assertIn("uniform sampler2D sampler;", src)
            self.assertIn("in vec2 texcoord0;", src)
            self.assertEqual(src.count("void main()"), 1)
            # premultiplied in, premultiplied and window opacity out
            self.assertIn("p.rgb / p.a", src)
            self.assertIn("vec4(fragColor.rgb * fragColor.a, fragColor.a) * modulation", src)

    def test_unexpected_shader_shape_is_refused(self):
        with self.assertRaises(ValueError):
            kwin_rabbit.kwin_shader("void main() {}", MARKER)

    @unittest.skipUnless(shutil.which("glslangValidator"), "glslangValidator not installed")
    def test_compiles_in_both_kwin_dialects(self):
        with tempfile.TemporaryDirectory() as d:
            for mode in kwin_rabbit.MODES:
                for version in ("#version 300 es", "#version 140"):
                    f = Path(d, f"{mode}.frag")
                    f.write_text(version + "\n" + self.shader(mode))
                    r = subprocess.run(["glslangValidator", str(f)], capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, f"{mode} {version}: {r.stdout}")


class EffectTests(unittest.TestCase):
    SRC = ROOT / "files/desktop/kwin-rabbit"

    def test_effect_reads_generated_shaders_and_shared_state(self):
        cpp = (self.SRC / "rabbit.cpp").read_text()
        self.assertIn('"/.local/share/t2-mac-kde/kwin-rabbit"', cpp)
        self.assertIn('"/hypr-nightmode"', cpp)
        self.assertIn('QStringLiteral(".frag")', cpp)
        for mode in kwin_rabbit.MODES:
            self.assertIn(f'QStringLiteral("{mode}")', cpp)
        self.assertIn("ShaderTrait::MapTexture | ShaderTrait::Modulate", cpp)

    def test_plugin_file_name_is_the_effect_id(self):
        self.assertIn('PREFIX ""', (self.SRC / "CMakeLists.txt").read_text())
        self.assertIn("add_library(t2rabbit MODULE", (self.SRC / "CMakeLists.txt").read_text())
        self.assertNotIn('"Id"', (self.SRC / "metadata.json").read_text())   # from the file name
        self.assertEqual(kwin_rabbit.EFFECT_ID, "t2rabbit")

    def test_dropin_puts_the_build_on_kwins_plugin_path(self):
        dropin = kwin_rabbit.kwin_dropin(MARKER)
        self.assertIn("Environment=QT_PLUGIN_PATH=%h/.local/lib/t2-mac-kde/qt6/plugins", dropin)
        build = (self.SRC / "build-kwin-rabbit").read_text()
        self.assertIn('out="$HOME/.local/lib/t2-mac-kde/qt6/plugins/kwin/effects/plugins"', build)
        self.assertIn("kwin-dev", build)

    def test_hypr_nightmode_works_outside_hyprland(self):
        tool = (ROOT / "files/desktop/bin/hypr-nightmode").read_text()
        self.assertRegex(tool, r'if \[ -n "\$\{HYPRLAND_INSTANCE_SIGNATURE:-\}" \]; then\n  hyprctl keyword')

    def test_deploy_wiring(self):
        task = (ROOT / "tasks/desktop.py").read_text()
        for needle in ('"extra-cmake-modules"', "build-kwin-rabbit", "kwin_rabbit.kwin_shader", "plasma-kwin_wayland.service.d",
                       "net.local.t2rabbit", '"kwin-dev"'):
            self.assertIn(needle, task)

    def test_panel_rabbit(self):
        qml = (ROOT / "files/desktop/plasma/net.local.t2rabbit/contents/ui/main.qml").read_text()
        self.assertIn("hypr-nightmode", qml)
        self.assertIn('root.setMode("off")', qml)          # right-click = off, as in Waybar
        for mode in ("off",) + kwin_rabbit.MODES:
            self.assertRegex(qml, rf'\["{mode}", ')


if __name__ == "__main__":
    unittest.main()

