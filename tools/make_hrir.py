#!/usr/bin/env python3
"""Build the true-stereo binaural IR for the EasyEffects convolver ("QC35 3D" preset).

    curl -fsSLo /tmp/kemar/diffuse.zip https://sound.media.mit.edu/resources/KEMAR/diffuse.zip
    python3 -I tools/make_hrir.py /tmp/kemar/diffuse.zip

Input: MIT Media Lab KEMAR HRTFs, diffuse-field equalized set (Gardner & Martin 1994; free use,
authors credited, see files/audio-effects/irs/CREDITS.txt). The zip is sha256-checked.
Output: files/audio-effects/irs/kemar_stereo_30deg.irs, a 4-channel 16-bit WAV (.irs is the
extension EasyEffects looks for) at 48 kHz (the PipeWire graph rate here), channel order as
EasyEffects 8 reads it: 0 = L in -> L ear, 1 = L in -> R ear, 2 = R in -> L ear, 3 = R in -> R ear.
Two virtual speakers at +-30 deg azimuth, 0 deg elevation. KEMAR "H0e030a" holds a source 30 deg
to the RIGHT (left channel = left ear); the left speaker is its mirror image (symmetric set).
Standard library only; deterministic.
"""
import argparse
import hashlib
import io
import math
import struct
import sys
import wave
import zipfile
from pathlib import Path

HRTF_URL = "https://sound.media.mit.edu/resources/KEMAR/diffuse.zip"
HRTF_SHA256 = "a48e73137390626ef1e45d1de6a4d98530c6aa570e71b40f7c4442241ed5fa22"
HRTF_MEMBER = "elev0/H0e030a.wav"
IN_RATE, OUT_RATE = 44100, 48000
PAD = 16             # leading zeros so the resampling kernel is not cut at t=0
HALF = 32            # windowed-sinc half width (input samples)
CUTOFF = 0.95        # fraction of the input Nyquist
PEAK = 10 ** (-1 / 20)  # normalize to -1 dBFS (EasyEffects autogain rescales anyway)
OUT = Path(__file__).resolve().parents[1] / "files/audio-effects/irs/kemar_stereo_30deg.irs"


def read_member(zip_path):
    data = Path(zip_path).read_bytes()
    if hashlib.sha256(data).hexdigest() != HRTF_SHA256:
        raise SystemExit(f"{zip_path}: sha256 does not match the pinned {HRTF_SHA256}")
    with zipfile.ZipFile(io.BytesIO(data)) as z, wave.open(io.BytesIO(z.read(HRTF_MEMBER))) as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (2, 2, IN_RATE):
            raise SystemExit(f"{HRTF_MEMBER}: unexpected format")
        n = w.getnframes()
        s = struct.unpack(f"<{2 * n}h", w.readframes(n))
    left_ear, right_ear = [x / 32768 for x in s[0::2]], [x / 32768 for x in s[1::2]]
    if sum(x * x for x in right_ear) <= sum(x * x for x in left_ear):
        raise SystemExit("expected the right ear to be ipsilateral for a source at 30 deg right")
    return right_ear, left_ear  # ipsilateral, contralateral


def _blackman(x):
    return 0.42 + 0.5 * math.cos(math.pi * x) + 0.08 * math.cos(2 * math.pi * x)


def resample(sig, rate_in=IN_RATE, rate_out=OUT_RATE):
    """Band-limited (windowed sinc) resampling; upsampling keeps unity gain."""
    sig = [0.0] * PAD + list(sig)
    n_out = math.ceil(len(sig) * rate_out / rate_in)
    out = []
    for n in range(n_out):
        pos = n * rate_in / rate_out
        acc = 0.0
        for k in range(max(0, math.floor(pos) - HALF + 1), min(len(sig), math.floor(pos) + HALF + 1)):
            d = pos - k
            if abs(d) >= HALF:
                continue
            arg = CUTOFF * d
            sinc = 1.0 if arg == 0 else math.sin(math.pi * arg) / (math.pi * arg)
            acc += sig[k] * CUTOFF * sinc * _blackman(d / HALF)
        out.append(acc)
    return out


def build(zip_path, out=OUT):
    ipsi, contra = (resample(x) for x in read_member(zip_path))
    channels = (ipsi, contra, contra, ipsi)  # LL, LR, RL, RR
    scale = PEAK / max(abs(v) for ch in channels for v in ch)
    frames = b"".join(struct.pack("<4h", *(round(ch[i] * scale * 32767) for ch in channels))
                      for i in range(len(ipsi)))
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(4)
        w.setsampwidth(2)
        w.setframerate(OUT_RATE)
        w.writeframes(frames)
    return hashlib.sha256(out.read_bytes()).hexdigest()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("zip", help=f"downloaded {HRTF_URL}")
    p.add_argument("--out", type=Path, default=OUT)
    a = p.parse_args(argv)
    print(f"{build(a.zip, a.out)}  {a.out}")


if __name__ == "__main__":
    sys.exit(main())
