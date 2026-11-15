"""Speaker DSP for the MacBookPro16,1 6-speaker array (config speaker_dsp, default off).

On: packages + per-user graph/FIRs + speakers-only WirePlumber drop-in. Off: the drop-in and
script are removed. Either change restarts WirePlumber (audio blips once). See manage/speaker_dsp.py.
"""
import os
from io import StringIO
from pathlib import Path

from pyinfra import logger
from pyinfra.operations import files, server
from pyinfra.operations.util import any_changed

from manage import speaker_dsp as sd
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context
from manage.userconfig import setting

validate_local_context()
home = os.path.expanduser("~")
src = Path(__file__).resolve().parents[1] / "files/speaker-dsp"
data_dir = f"{home}/.local/share/t2-mac-kde/speaker-dsp/{sd.MODEL_DIR}"
conf = f"{home}/.config/wireplumber/wireplumber.conf.d/{sd.CONF}"
script = f"{home}/.local/share/wireplumber/scripts/{sd.SCRIPT}"
model = Path("/sys/class/dmi/id/product_name").read_text().strip() if os.path.exists("/sys/class/dmi/id/product_name") else ""
wanted = bool(setting("speaker_dsp", False)) and model == sd.MODEL

if wanted:
    install_packages(PackageRequest(packages=sd.PACKAGES))
    ops = [files.put(name=f"Speaker DSP: {wav.name}", src=str(wav), dest=f"{data_dir}/{wav.name}",
                     mode="644", create_remote_dir=True) for wav in sorted((src / sd.MODEL_DIR).glob("*.wav"))]
    ops.append(files.put(name="Speaker DSP: graph.json (per-user FIR paths)", dest=f"{data_dir}/graph.json", mode="644",
                         src=StringIO(sd.graph((src / sd.MODEL_DIR / "graph.json").read_text(), data_dir)),
                         create_remote_dir=True))
    ops.append(files.put(name="Speaker DSP: LICENSE note", src=str(src / "COPYRIGHT"), dest=f"{data_dir}/COPYRIGHT",
                         mode="644", create_remote_dir=True))
    ops.append(files.put(name=f"WirePlumber: {sd.SCRIPT} (speakers-only unity route)", src=str(src / sd.SCRIPT),
                         dest=script, mode="644", create_remote_dir=True))
    ops.append(files.put(name=f"WirePlumber drop-in {sd.CONF} (speaker DSP, speakers only)",
                         src=StringIO(sd.wireplumber_conf(f"{data_dir}/graph.json")), dest=conf, mode="644",
                         create_remote_dir=True))
    changed = any_changed(*ops)
else:
    if model != sd.MODEL and setting("speaker_dsp", False):
        logger.warning(f"speaker_dsp: no config for {model or 'this model'}; only {sd.MODEL} is supported")
    ops = [files.file(name=f"Speaker DSP off: remove {sd.CONF}", path=conf, present=False),
           files.file(name=f"Speaker DSP off: remove {sd.SCRIPT}", path=script, present=False)]
    changed = any_changed(*ops)

server.shell(name="Restart WirePlumber (speaker DSP changed; audio blips once)",
             commands=["systemctl --user restart wireplumber.service"], _if=changed)
