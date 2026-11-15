"""EasyEffects 8 presets for the Bose QC35 (Boom3D-like) and Bypass for the T2 sinks (pure, offline).

Formats checked against easyeffects v8.1.2 (src/*_preset.cpp, contents/kcfg/*.kcfg,
presets_directory_manager.cpp, presets_autoload_manager.cpp):
- presets   ~/.local/share/easyeffects/output/<name>.json  {"output": {"blocklist", "plugins_order", "<plugin>#0"}}
- IRs       ~/.local/share/easyeffects/irs/<kernel-name>.irs (WAV; 4 channels = LL, LR, RL, RR)
- autoload  ~/.local/share/easyeffects/autoload/output/<node.name>:<route description>.json
            ("/" replaced by "_"; route = the device's active output Route description)
- settings  ~/.config/easyeffects/db/easyeffectsrc (KConfig)
"""
import json
import math
import re

AUTOEQ_COMMIT = "0fad4b2ce4b3ceb97f0086c3a0940b4c2473c1f3"
AUTOEQ_FILE = "Bose QuietComfort 35 (wireless) ParametricEQ.txt"
AUTOEQ_SHA256 = "791b7268e74a50e1e4b215f78aefc0337a4f1457afb8d67420b43fbf04d64523"
IR_NAME = "kemar_stereo_30deg"
IR_SHA256 = "131c76e7c73aa0235945f12d71e2386e2552a63662a4ce14cd34f06ee5137828"

PRESET_3D, PRESET_BYPASS = "QC35 3D", "Bypass"
PLUGINS_3D = ("equalizer#0", "bass_enhancer#0", "crossfeed#0", "convolver#0", "limiter#0")
PACKAGES = ("easyeffects",
            "lsp-plugins-lv2",  # equalizer (para_equalizer_x32_lr) + limiter (sc_limiter_stereo)
            "calf-plugins")     # bass enhancer (calf BassEnhancer); crossfeed/convolver are built in

# Bose Corporation OUIs, checked against /usr/share/ieee-data/oui.txt (E4:58:BC is not Bose there).
BOSE_OUIS = ("00:0C:8A", "04:52:C7", "08:DF:1F", "28:11:A5", "2C:41:A1", "4C:87:5D",
             "60:AB:D2", "78:2B:64", "AC:BF:71", "BC:87:FA", "C8:7B:23")
A2DP_SINK_UUID = "0000110b-0000-1000-8000-00805f9b34fb"
# SPA bluez5 names the A2DP output route "Headphones" for headphone and headset form factors
# (pipewire 1.6.2 bluez5-device.c; observed live: route headphone-output "Headphones").
BT_ROUTE = "Headphones"

# T2 sinks (package-owned UCM split chain). Both sinks belong to one ALSA card, so EasyEffects
# sees that card's active route for either of them: cover both route descriptions.
T2_SINKS = {
    "alsa_output.pci-0000_04_00.3.HiFi__Speaker__sink": "Apple Audio Device Internal Speakers",
    "alsa_output.pci-0000_04_00.3.HiFi__Headphones__sink": "Apple Audio Device Headphones",
}
T2_ROUTES = ("Internal Speakers", "Headphones")

WET = 0.85  # "3D effect" ~85 %
_BAND_TYPES = {"PK": "Bell", "LSC": "Lo-shelf", "HSC": "Hi-shelf", "LS": "Lo-shelf", "HS": "Hi-shelf"}
_FILTER = re.compile(r"^Filter\s+\d+:\s+ON\s+(\w+)\s+Fc\s+([\d.]+)\s+Hz\s+Gain\s+(-?[\d.]+)\s+dB\s+Q\s+([\d.]+)\s*$")


def parse_parametric_eq(text):
    """AutoEq ParametricEQ.txt -> (preamp dB, [(type, freq, gain, q)])."""
    preamp, filters = None, []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("Preamp:"):
            preamp = float(line.split()[1])
            continue
        m = _FILTER.match(line)
        if not m or m[1] not in _BAND_TYPES:
            raise ValueError(f"unsupported AutoEq line: {line!r}")
        filters.append((_BAND_TYPES[m[1]], float(m[2]), float(m[3]), float(m[4])))
    if preamp is None or not 1 <= len(filters) <= 32:
        raise ValueError("AutoEq file needs a Preamp line and 1..32 filters")
    return preamp, filters


def _equalizer(preamp, filters):
    # "APO (DR)" = Equalizer APO's biquads, which AutoEq's parametric filters are fitted for.
    channel = {f"band{i}": {"type": t, "mode": "APO (DR)", "slope": "x1", "solo": False, "mute": False,
                            "gain": g, "frequency": f, "q": q, "width": 4.0}
               for i, (t, f, g, q) in enumerate(filters)}
    return {"bypass": False, "input-gain": preamp, "output-gain": 0.0, "mode": "IIR",
            "split-channels": False, "balance": 0.0, "pitch-left": 0.0, "pitch-right": 0.0,
            "num-bands": len(filters), "left": channel, "right": json.loads(json.dumps(channel))}


def _db(ratio):
    return round(20 * math.log10(ratio), 1)


def preset_3d(autoeq_text, boost_db=0.0):
    """boost_db: extra level into the limiter (config music_boost_db); peaks stay at -1 dB."""
    preamp, filters = parse_parametric_eq(autoeq_text)
    out = {"blocklist": [], "plugins_order": list(PLUGINS_3D)}
    out["equalizer#0"] = _equalizer(preamp, filters)
    # Boom3D "bass boost": Calf harmonics below 100 Hz, moderate amount (+4 dB); a low-shelf would
    # add real LF energy the SBC link and the QC35 driver then compress.
    out["bass_enhancer#0"] = {"bypass": False, "input-gain": 0.0, "output-gain": 0.0, "amount": 4.0,
                              "harmonics": 8.5, "scope": 100.0, "floor": 20.0, "blend": 0.0,
                              "floor-active": False}
    out["crossfeed#0"] = {"bypass": False, "input-gain": 0.0, "output-gain": 0.0, "fcut": 700, "feed": 4.5}
    # dry/wet are dB gains: 85 % wet = -1.4 dB, 15 % dry = -16.5 dB.
    out["convolver#0"] = {"bypass": False, "input-gain": 0.0, "output-gain": 0.0, "kernel-name": IR_NAME,
                          "ir-width": 100, "autogain": True, "dry": _db(1 - WET), "wet": _db(WET),
                          "sofa": {"azimuth": 0.0, "elevation": 0.0, "radius": 1.0}}
    out["limiter#0"] = {"mode": "Herm Thin", "oversampling": "None", "dithering": "None",
                        "sidechain-type": "Internal", "bypass": False, "input-gain": float(boost_db), "output-gain": 0.0,
                        "lookahead": 5.0, "attack": 5.0, "release": 20.0, "threshold": -1.0,
                        "sidechain-preamp": 0.0, "stereo-link": 100.0, "alr-attack": 5.0, "alr-release": 50.0,
                        "alr-knee": 0.0, "alr-knee-smooth": -5.0, "alr": False,
                        "gain-boost": False,  # true would lift the output back up to 0 dBFS
                        "input-to-sidechain": 0.0, "input-to-link": 0.0, "sidechain-to-input": 0.0,
                        "sidechain-to-link": 0.0, "link-to-input": 0.0, "link-to-sidechain": 0.0}
    return {"output": out}


def preset_bypass():
    return {"output": {"blocklist": [], "plugins_order": []}}


def dumps(data):
    return json.dumps(data, indent=4) + "\n"


def autoload_entry(node, description, route, preset):
    """(file name, json) as written by EasyEffects' AutoloadManager::add."""
    name = f"{node.replace('/', '_')}:{route.replace('/', '_')}.json"
    return name, {"device": node, "device-description": description, "device-profile": route,
                  "preset-name": preset}


def t2_autoloads():
    return [autoload_entry(node, desc, route, PRESET_BYPASS) for node, desc in T2_SINKS.items() for route in T2_ROUTES]


def bt_sink_node(mac):
    """User-visible WirePlumber sink (the internal one is bluez_output.<MAC_>.1, Audio/Sink/Internal)."""
    return f"bluez_output.{mac.upper()}"


def parse_devices(text):
    """`bluetoothctl devices [Paired]` -> [(MAC, name)]."""
    found = []
    for line in text.splitlines():
        m = re.match(r"^Device\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})\s*(.*)$", line.strip())
        if m:
            found.append((m[1].upper(), m[2]))
    return found


def is_bose(mac):
    return mac.upper()[:8] in BOSE_OUIS


def parse_info(text):
    """`bluetoothctl info MAC` -> (has A2DP sink, trusted, alias)."""
    alias = re.search(r"^\s*Alias:\s*(.*)$", text, re.M)
    return (A2DP_SINK_UUID in text.lower(),
            bool(re.search(r"^\s*Trusted:\s*yes", text, re.M)),
            alias[1].strip() if alias else "")


# EasyEffects settings this module owns (group, key, value); everything else stays the user's.
DB_SETTINGS = (
    ("Window", "outputAutoloadingUsesFallback", "true"),     # unknown output devices -> Bypass
    ("Window", "outputAutoloadingFallbackPreset", PRESET_BYPASS),
    ("Window", "autostartOnLogin", "false"),                 # never an XDG autostart (KDE login)
)


def set_kconfig(text, settings):
    """Set group/key=value in KConfig ini text, keeping every other line."""
    lines = text.splitlines()
    for group, key, value in settings:
        header = f"[{group}]"
        try:
            start = lines.index(header)
        except ValueError:
            if lines and lines[-1].strip():
                lines.append("")
            lines += [header, f"{key}={value}"]
            continue
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))
        for i in range(start + 1, end):
            if lines[i].split("=", 1)[0].strip() == key:
                lines[i] = f"{key}={value}"
                break
        else:
            while end > start + 1 and not lines[end - 1].strip():
                end -= 1
            lines.insert(end, f"{key}={value}")
    return "\n".join(lines) + "\n"


def bose_macs(devices_text, info_of, configured=None):
    """Paired music headphones with an A2DP sink.

    configured: config `music_headphones` (MACs and/or device names/aliases, any case);
    unset -> every paired Bose (OUI). info_of(mac) -> `bluetoothctl info` text.
    Returns [(MAC, alias, trusted)].
    """
    wanted = {str(m).strip().lower() for m in ([configured] if isinstance(configured, str) else configured or [])}
    found = []
    for mac, _name in parse_devices(devices_text):
        sink, trusted, alias = parse_info(info_of(mac))
        names = {mac.lower(), (_name or "").lower(), (alias or "").lower()}
        if sink and ((names & wanted) if wanted else is_bose(mac)):
            found.append((mac, alias or _name, trusted))
    return found


# --- WirePlumber 0.5 (user drop-in): Bose = music only ---------------------------------------------
WP_CONF = "60-t2-bluetooth-roles.conf"
WP_SCRIPT = "t2-bose-mic-never-default.lua"


def wireplumber_conf(macs):
    """SPA-JSON drop-in for ~/.config/wireplumber/wireplumber.conf.d (merged into the system config).

    - monitor.bluez.rules: the Bose card only auto-(re)connects A2DP (no HFP/HSP from our side).
    - device.profile.priority.rules: A2DP is its preferred profile on connect.
    - the Lua hook drops its microphone from default-source selection, so call apps use the
      internal mic and WirePlumber's headset autoswitch (triggered only by a capture link to that
      mic) never fires for it. AirPods/other headsets keep the defaults.
    """
    cards = "\n".join(f'      {{ device.name = "bluez_card.{m.replace(":", "_")}" }}' for m in macs)
    return f"""# Managed by t2-mac-kde (tasks/audio_effects.py). Bose QC35 = music only.
monitor.bluez.rules = [
  {{
    matches = [
{cards}
    ]
    actions = {{
      update-props = {{
        bluez5.auto-connect = [ a2dp_sink ]
      }}
    }}
  }}
]

device.profile.priority.rules = [
  {{
    matches = [
{cards}
    ]
    actions = {{
      update-props = {{
        priorities = [ a2dp-sink, a2dp-sink-sbc_xq ]
      }}
    }}
  }}
]

wireplumber.components = [
  {{
    name = {WP_SCRIPT}, type = script/lua
    provides = custom.t2-bose-mic-never-default
  }}
]

wireplumber.profiles = {{
  main = {{
    custom.t2-bose-mic-never-default = optional
  }}
}}
"""


def wireplumber_script(macs):
    prefixes = []
    for m in macs:
        prefixes += [f"bluez_input.{m}", f"bluez_input.{m.replace(':', '_')}"]
    table = ", ".join(f'"{p}"' for p in prefixes)
    return f"""-- Managed by t2-mac-kde (tasks/audio_effects.py). Bose QC35 = music only:
-- its Bluetooth microphone is never chosen as the default source (calls use the internal mic).
local prefixes = {{ {table} }}

local function is_bose_mic (name)
  for _, p in ipairs (prefixes) do
    if name and name:sub (1, #p) == p then
      return true
    end
  end
  return false
end

SimpleEventHook {{
  name = "t2/bose-mic-never-default",
  before = {{ "default-nodes/find-selected-default-node", "default-nodes/find-best-default-node" }},
  interests = {{
    EventInterest {{
      Constraint {{ "event.type", "=", "select-default-node" }},
      Constraint {{ "default-node.type", "=", "audio.source" }},
    }},
  }},
  execute = function (event)
    local nodes = event:get_data ("available-nodes")
    nodes = nodes and nodes:parse ()
    if not nodes then
      return
    end
    local keep = {{}}
    for _, props in ipairs (nodes) do
      if not is_bose_mic (props ["node.name"]) then
        table.insert (keep, Json.Object (props))
      end
    end
    event:set_data ("available-nodes", Json.Array (keep))
  end
}}:register ()
"""
