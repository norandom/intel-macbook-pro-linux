"""The rabbit's screen filters in KDE: Hyprland's shaders rewritten for the KWin effect.

Hyprland runs files/desktop/hypr/shaders/night-<mode>.glsl over the finished screen
(decoration:screen_shader). KWin has no such hook; the t2rabbit effect
(files/desktop/kwin-rabbit) draws every window through the same filter instead. KWin's
window shaders differ in four ways, rewritten here at deploy time:
- the GLSL version is KWin's (the effect prepends "#version 140" or "#version 300 es");
- the texture is "sampler" and the coordinate "texcoord0" (KWin's MapTexture vertex shader);
- window textures are premultiplied: filter the straight colour, premultiply afterwards;
- window opacity comes in as "modulation" (ShaderTrait::Modulate).
The mode stays ~/.local/state/hypr-nightmode, shared with Hyprland.
"""
import re

MODES = ("green", "dark", "grayscale", "monochrome", "warmwhite")
EFFECT_ID = "t2rabbit"
DROPIN = "t2-rabbit.conf"
PLUGIN_PATH = "%h/.local/lib/t2-mac-kde/qt6/plugins"   # build-kwin-rabbit installs kwin/effects/plugins/t2rabbit.so here

_TEXEL = ("uniform sampler2D sampler;\nuniform vec4 modulation;\n"
          "vec4 t2_texel(vec2 c) { vec4 p = texture(sampler, c); return p.a > 0.0 ? vec4(p.rgb / p.a, p.a) : p; }")
_MAIN = "\nvoid main() { t2_filter(); t2_out = vec4(fragColor.rgb * fragColor.a, fragColor.a) * modulation; }\n"


def kwin_shader(src: str, marker: str) -> str:
    """Fragment shader for KWin without its #version line (the effect adds KWin's)."""
    for needed in ("uniform sampler2D tex;", "in vec2 v_texcoord;", "out vec4 fragColor;", "void main()"):
        if src.count(needed) != 1:
            raise ValueError(f"shader not in the expected Hyprland shape: {needed!r}")
    src = re.sub(r"^\s*#version[^\n]*\n", "", src)
    src = (src.replace("in vec2 v_texcoord;", "in vec2 texcoord0;")
              .replace("v_texcoord", "texcoord0")
              .replace("textureSize(tex,", "textureSize(sampler,")
              .replace("texture(tex,", "t2_texel(")
              .replace("uniform sampler2D tex;", _TEXEL)
              .replace("out vec4 fragColor;", "out vec4 t2_out;\nvec4 fragColor;")
              .replace("void main()", "void t2_filter()"))
    if re.search(r"\btex\b", src):
        raise ValueError("shader uses the Hyprland texture in a way not rewritten")
    return f"// {marker}: generated from the Hyprland shader (manage/kwin_rabbit.py)\n" + src + _MAIN


def kwin_dropin(marker: str) -> str:
    """KWin finds effect plugins only on Qt's plugin path; add ours (the system one stays)."""
    return (f"# {marker}: the t2rabbit effect (the rabbit's screen filters in KDE).\n"
            f"[Service]\nEnvironment=QT_PLUGIN_PATH={PLUGIN_PATH}\n")
