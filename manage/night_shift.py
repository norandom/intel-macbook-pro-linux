"""Night shift (config night_shift): warmer screen colours after sunset, gammastep.

gammastep follows the sun at a fixed location (no geoclue, nothing sent anywhere) and fades
through dusk and dawn. Location: config night_shift_location "lat:lon", else the coordinates
of the system timezone's city from /usr/share/zoneinfo (Europe/Berlin -> 52.50:13.37).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ZONE_TABLES = ("/usr/share/zoneinfo/zone1970.tab", "/usr/share/zoneinfo/zone.tab")
_ISO6709 = re.compile(r"^([+-])(\d{2})(\d{2})(\d{2})?([+-])(\d{3})(\d{2})(\d{2})?$")
_LOC = re.compile(r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*:\s*(-?\d{1,3}(?:\.\d+)?)\s*$")


def iso6709(text: str) -> tuple[float, float]:
    m = _ISO6709.match(text)
    if not m:
        raise ValueError(f"not an ISO 6709 coordinate: {text!r}")
    s1, d1, m1, x1, s2, d2, m2, x2 = m.groups()
    lat = int(d1) + int(m1) / 60 + int(x1 or 0) / 3600
    lon = int(d2) + int(m2) / 60 + int(x2 or 0) / 3600
    return round(-lat if s1 == "-" else lat, 2), round(-lon if s2 == "-" else lon, 2)


def timezone_location(tz: str | None = None, tables=ZONE_TABLES) -> tuple[float, float] | None:
    if tz is None:
        tz = subprocess.run(["timedatectl", "show", "-p", "Timezone", "--value"],
                            capture_output=True, text=True).stdout.strip()
        if not tz:
            try:
                tz = Path("/etc/timezone").read_text().strip()
            except OSError:
                return None
    for table in tables:
        try:
            lines = Path(table).read_text().splitlines()
        except OSError:
            continue
        for line in lines:
            cols = line.split("\t")
            if len(cols) >= 3 and not line.startswith("#") and cols[2] == tz:
                return iso6709(cols[1])
    return None


def location(value: str, tz: str | None = None) -> tuple[float, float]:
    if value:
        m = _LOC.match(value)
        if not m:
            raise ValueError('night_shift_location must look like "52.52:13.40" (latitude:longitude)')
        lat, lon = float(m.group(1)), float(m.group(2))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("night_shift_location out of range")
        return lat, lon
    loc = timezone_location(tz)
    if not loc:
        raise ValueError('night_shift: no location; set night_shift_location = "lat:lon"')
    return loc


def config_ini(lat: float, lon: float, day: int, night: int) -> str:
    for name, k in (("night_shift_day", day), ("night_shift_night", night)):
        if not isinstance(k, int) or not 1000 <= k <= 25000:
            raise ValueError(f"{name} must be a temperature in K (1000-25000)")
    return ("; Managed by t2-mac-kde (desktop). From config.toml night_shift*; edit that, not this file.\n"
            "[general]\n"
            f"temp-day={day}\n"
            f"temp-night={night}\n"
            "fade=1\n"
            "adjustment-method=wayland\n"
            "location-provider=manual\n\n"
            "[manual]\n"
            f"lat={lat}\n"
            f"lon={lon}\n")
