# Audio

Two independent parts: a 3D chain for music headphones (`tasks/audio_effects.py`, EasyEffects)
and a DSP for the built-in speakers (`tasks/speaker_dsp.py`, WirePlumber). Neither touches the
system PipeWire, WirePlumber or ALSA UCM files; everything is per user.

## Headphone presets

EasyEffects runs as a user service inside the Hyprland session only. In KDE it doesn't start,
so the headphones play unprocessed there.

Every preset starts from the same chain: AutoEq correction for the Bose QC35, bass enhancer,
crossfeed, a binaural convolver (MIT KEMAR at 85 % wet) and a limiter at -1 dB. The variants
add a room:

| Config `music_preset` | `hypr-3d` | What it adds |
|---|---|---|
| `plain` (default) | `plain` | Nothing: the 3D chain on its own |
| `room` | `room` | Short room reverb, more spherical, closest to Boom3D |
| `stage` | `stage` | More space than room, vocals kept in front (my pick) |
| `room+` | `plus` | Room plus exciter and a gentle maximizer |
| `auditorium` | `auditorium` | A measured head-and-room response (ASH Listening Set, CC BY-NC-SA, downloaded at deploy) |

I tuned it on Therion and Hans Zimmer, so dense passages keep their punch instead of turning
into mush.

```sh
hypr-3d stage    # switch the preset live
hypr-3d off      # effects off for a straight A/B comparison
hypr-3d on
hypr-3d status
```

`music_boost_db` adds level for the music headphones (+2 dB is about 20 % louder); the limiter
still caps peaks.

## Music headphones vs headsets

The deploy treats some Bluetooth devices as music headphones:

- they get the configured preset automatically when they connect;
- they're trusted, so A2DP reconnects by itself;
- they stay in A2DP music mode, never the call profile, and their microphone never becomes the
  default input.

Which devices: `music_headphones = ["My QC35"]` (names or MACs as shown by
`bluetoothctl devices`). Unset, every paired Bose device counts. Everything else, a headset such
as AirPods, stays a normal headset that can take calls. The internal mic and speakers work for
calls without any of this.

Pair the headphones first, then re-run `tasks/audio_effects.py`. `music_codec = "sbc_xq"` sounds
cleaner but can tick when Wi-Fi is on 2.4 GHz.

The built-in speakers and the T2 headphone jack always load the empty `Bypass` preset, and so
does any device the deploy doesn't know.

## Speaker DSP (MacBookPro16,1)

The six built-in speakers sound thin on Linux without processing. With `speaker_dsp = true` they
get the t2linux DSP from [lemmyg/t2-apple-audio-dsp](https://github.com/lemmyg/t2-apple-audio-dsp):
an FIR crossover, bass enhancement (bankstown) and a limiter, similar to what macOS does behind
the scenes. It's a WirePlumber drop-in for the speakers only, so it works in KDE and Hyprland.

The task checks the DMI model and does nothing on other Macs. `speaker_dsp = false` and a re-run
removes the drop-in. Each change restarts WirePlumber, so audio blips once.

## Change it

| You want | Change |
|---|---|
| Another preset by default | `music_preset` |
| Other headphones counted as music headphones | `music_headphones` |
| An EQ curve for your own headphones | replace the file in `files/audio-effects/autoeq/` (an AutoEq `ParametricEQ.txt`) and update `AUTOEQ_FILE` and `AUTOEQ_SHA256` in `manage/audio_effects.py` |
| Different chain or room settings | the `preset_*` functions in `manage/audio_effects.py` |
| Speaker DSP on or off | `speaker_dsp` |

Without your own AutoEq file, any headphones in `music_headphones` get the QC35 correction curve.

Re-run: `.venv/bin/pyinfra @local tasks/audio_effects.py --use-sudo-password` (and
`tasks/speaker_dsp.py` for the speakers).
