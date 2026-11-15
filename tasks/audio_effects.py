"""Boom3D-like sound for the Bose QC35 via EasyEffects 8; T2 speakers stay untouched.

Run: .venv/bin/pyinfra @local tasks/audio_effects.py [--dry] [--use-sudo-password]

- apt (guarded): easyeffects + lsp-plugins-lv2 (EQ, limiter) + calf-plugins (bass enhancer).
- User files only (~/.local/share/easyeffects, ~/.config/easyeffects/db): presets "QC35 3D"
  (AutoEq EQ -> bass enhancer -> crossfeed -> KEMAR convolver 85 % wet -> limiter -1 dB) and
  "Bypass" (empty chain); autoload Bypass for the T2 speaker/headphone sinks and as the fallback
  for every other device. No PipeWire/WirePlumber/UCM system file is touched.
- Music headphones (config music_headphones: MACs or names; default any paired Bose): autoload "QC35 3D" on its sink,
  `bluetoothctl trust` so A2DP reconnects, and a user WirePlumber drop-in (music only: A2DP
  auto-connect, its mic never becomes the default source). WirePlumber restarts only when that
  drop-in changed (brief audio interruption).
- easyeffects.service (service mode) wanted by hypr-desktop.target only; ~/.local/bin/hypr-3d.
Pure logic + pins: manage/audio_effects.py. IR builder: tools/make_hrir.py.
"""
import hashlib
import os
import subprocess
from io import StringIO
from pathlib import Path

from pyinfra import host, local, logger
from pyinfra.operations import files, server
from pyinfra.operations.util import any_changed

from manage import audio_effects as ae
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
local.include("tasks/package_policy.py")

project = Path(__file__).resolve().parents[1]
src = project / "files/audio-effects"
home = os.path.expanduser("~")
data = f"{home}/.local/share/easyeffects"
cfg = f"{home}/.config"
eq_file = src / "autoeq" / ae.AUTOEQ_FILE
ir_file = src / "irs" / f"{ae.IR_NAME}.irs"
for path, sha in ((eq_file, ae.AUTOEQ_SHA256), (ir_file, ae.IR_SHA256)):
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
        raise RuntimeError(f"{path.name} does not match its pinned sha256 (manage/audio_effects.py).")

install_packages(PackageRequest(packages=ae.PACKAGES, source="ubuntu"))


def put(content, dest, mode="644", name=None):
    return files.put(name=name or f"EasyEffects: {dest.replace(home, '~')}", src=StringIO(content), dest=dest,
                     mode=mode, create_remote_dir=True)


# --- Presets, IR, Bypass autoloads (always) ------------------------------------------------------
boost = float(setting("music_boost_db", 0))
# music_preset: "plain" = QC35 3D, "room" = QC35 3D Room (short reverb); hypr-3d room|plain switches live.
music_preset = ae.PRESET_3D_ROOM if str(setting("music_preset", "plain")) == "room" else ae.PRESET_3D
ee_ops = [put(ae.dumps(ae.preset_3d(eq_file.read_text(), boost)), f"{data}/output/{ae.PRESET_3D}.json"),
          put(ae.dumps(ae.preset_3d_room(eq_file.read_text(), boost)), f"{data}/output/{ae.PRESET_3D_ROOM}.json"),
          put(ae.dumps(ae.preset_bypass()), f"{data}/output/{ae.PRESET_BYPASS}.json")]
files.put(name=f"EasyEffects IR: {ae.IR_NAME}.irs (MIT KEMAR, +-30 deg)", src=str(ir_file),
          dest=f"{data}/irs/{ae.IR_NAME}.irs", mode="644", create_remote_dir=True)
for fname, entry in ae.t2_autoloads():
    put(ae.dumps(entry), f"{data}/autoload/output/{fname}", name=f"Autoload Bypass: {fname}")


db_path = Path(cfg, "easyeffects/db/easyeffectsrc")
db_old = db_path.read_text() if db_path.is_file() else ""
db_new = ae.set_kconfig(db_old, ae.DB_SETTINGS)
db_op = None
if db_new != db_old:  # EasyEffects owns the rest of this file: only rewrite when our keys differ
    db_op = put(db_new, str(db_path), name="EasyEffects: unknown devices fall back to Bypass, no XDG autostart")
# EasyEffects would autostart in KDE through this file; the session unit below replaces it.
files.file(name="No EasyEffects XDG autostart (KDE)", path=f"{cfg}/autostart/com.github.wwmm.easyeffects.desktop",
           present=False)

# --- Paired Bose -> autoload + trust + WirePlumber music-only drop-in ----------------------------


def _bt(*args):
    try:
        return subprocess.run(["bluetoothctl", *args], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


bose = ae.bose_macs(_bt("devices", "Paired"), lambda mac: _bt("info", mac), setting("music_headphones", setting("qc35_mac")))
wp_conf = f"{cfg}/wireplumber/wireplumber.conf.d/{ae.WP_CONF}"
wp_script = f"{home}/.local/share/wireplumber/scripts/{ae.WP_SCRIPT}"
if bose:
    for mac, alias, trusted in bose:
        fname, entry = ae.autoload_entry(ae.bt_sink_node(mac), alias, ae.BT_ROUTE, music_preset)
        put(ae.dumps(entry), f"{data}/autoload/output/{fname}", name=f"Autoload {music_preset}: {fname}")
        if not trusted:
            server.shell(name=f"bluetoothctl trust {mac} (A2DP auto-reconnect)", commands=[f"bluetoothctl trust {mac}"])
    macs = [m for m, _a, _t in bose]
    wp_ops = [put(ae.wireplumber_conf(macs), wp_conf, name=f"WirePlumber drop-in {ae.WP_CONF} (Bose = music only)"),
              put(ae.wireplumber_script(macs), wp_script, name=f"WirePlumber hook {ae.WP_SCRIPT}")]
    server.shell(name="Restart WirePlumber (drop-in changed; audio pauses for a moment)",
                 commands=["systemctl --user restart wireplumber.service"],
                 _if=any_changed(*wp_ops))
else:
    logger.info("Pair the QC35, then re-run tasks/audio_effects.py")

# --- Session service + toggle ---------------------------------------------------------------------
files.put(name="~/.local/bin/hypr-3d (3D on/off/status)", src=str(src / "hypr-3d"), dest=f"{home}/.local/bin/hypr-3d",
          mode="755", create_remote_dir=True)
unit = files.put(name="User unit easyeffects.service (Hyprland session only)", src=str(src / "easyeffects.service"),
                 dest=f"{cfg}/systemd/user/easyeffects.service", mode="644", create_remote_dir=True)
server.shell(name="systemd --user daemon-reload (easyeffects unit changed)", commands=["systemctl --user daemon-reload"],
             _if=unit.did_change)
server.shell(name="easyeffects.service wanted by hypr-desktop.target (no --now)",
             commands=["systemctl --user enable easyeffects.service"])
server.shell(name="(Re)start EasyEffects in a running Hyprland session",
             commands=["! systemctl --user is-active -q hypr-desktop.target || "
                       "systemctl --user restart easyeffects.service"],
             _if=any_changed(*[o for o in (unit, db_op, *ee_ops) if o]))
server.shell(name="Start EasyEffects in a running Hyprland session (if not running)",
             commands=["! systemctl --user is-active -q hypr-desktop.target || "
                       "systemctl --user start easyeffects.service"])
logger.info("audio_effects: `hypr-3d on|off|status` toggles the QC35 3D sound (EasyEffects global bypass).")
