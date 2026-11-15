"""MacBookPro16,1 speaker DSP (FIR crossover + bankstown bass + limiter), speakers only.

Taken from lemmyg/t2-apple-audio-dsp v1.1.0 (MIT, Asahi-based; files/speaker-dsp/), installed
per user instead of its .deb, whose postinst also enables the mic DSP and writes into
/usr/share/wireplumber. Revert = remove the drop-in (config speaker_dsp = false) and restart
WirePlumber: the raw 6-channel speaker sink comes back unchanged.
"""
import json

MODEL = "MacBookPro16,1"
MODEL_DIR = "16_1"
CONF = "51-t2-speaker-dsp.conf"
SCRIPT = "t2-speaker-unmute.lua"
PACKAGES = ("bankstown-lv2", "swh-lv2", "lsp-plugins-lv2",
            "libspa-0.2-modules-extra", "libpipewire-0.3-modules-extra")
UPSTREAM_DIR = f"/usr/share/t2-linux-audio/{MODEL_DIR}"


def graph(text: str, data_dir: str) -> str:
    """The upstream graph with its FIR paths pointed at the per-user copy."""
    out = text.replace(UPSTREAM_DIR, data_dir)
    json.loads(out)  # still valid JSON
    return out


def wireplumber_conf(graph_path: str) -> str:
    return f"""# Managed by t2-mac-kde (tasks/speaker_dsp.py): MacBookPro16,1 speaker DSP, speakers only.
# From lemmyg/t2-apple-audio-dsp (MIT). Delete this file and restart WirePlumber to revert.
monitor.alsa.rules = [
  {{
    matches = [
      {{
        api.alsa.card.name = "Apple T2 Audio"
        node.name = "~alsa_output.pci.*.HiFi__Speaker__sink"
        media.class = "Audio/Sink"
      }}
    ]
    actions = {{
      update-props = {{
        audio.allowed-rates = [48000, 44100]
        node.name = "alsa_output.platform-sound.RawSpeakers"
        node.description = "Raw Speaker Device (do not use)"
        node.nick = "RawSpeakers"
      }}
    }}
  }}
]

node.software-dsp.rules = [
  {{
    matches = [ {{ node.name = "alsa_output.platform-sound.RawSpeakers" }} ]
    actions = {{
      create-filter = {{
        filter-path = "{graph_path}"
        hide-parent = true
      }}
    }}
  }}
]

wireplumber.components = [
  {{
    name = {SCRIPT}, type = script/lua,
    provides = custom.t2-speaker-dsp
  }}
]

wireplumber.profiles = {{
  main = {{
    node.software-dsp = required
    custom.t2-speaker-dsp = required
  }}
}}
"""
