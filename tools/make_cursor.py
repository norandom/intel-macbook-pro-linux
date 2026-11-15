#!/usr/bin/env python3
"""Generate the "t2-highvis" Xcursor theme: big white arrow, black edge, thick red outline.

Accessibility aid (owner request): like Windows' large / coloured pointer. Pure stdlib,
deterministic. Writes files/desktop/cursors/t2-highvis/{index.theme,cursors/left_ptr}
plus links for the other names that mean "normal arrow". Other shapes (text beam, hand,
resize) inherit from breeze_cursors via index.theme.

    python3 tools/make_cursor.py
"""
import math
from pathlib import Path
import struct

OUT = Path(__file__).resolve().parents[1] / "files/desktop/cursors/t2-highvis"
SIZES = (32, 48, 64, 96, 128)          # nominal sizes; XCURSOR_SIZE picks the nearest
RED = (230, 20, 20)
ARROW = [(0, 0), (0, 17), (4.2, 13.2), (7, 19.5), (9.6, 18.4), (6.9, 12.2), (12.4, 12.2)]  # 20-unit design
ALIASES = ("default", "arrow", "top_left_arrow", "left_arrow", "pointer-default")


def _inside(x, y, poly):
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def _edge_distance(x, y, poly):
    best = math.inf
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return best


def render(size):
    """ARGB (premultiplied) pixels, hotspot. Arrow ~0.8 of the cursor box, red ring outside."""
    scale = size * 0.78 / 20.0
    ring, edge = max(2.0, size * 0.09), max(1.0, size * 0.035)
    pad = ring + 1
    poly = [(pad + x * scale, pad + y * scale) for x, y in ARROW]
    pixels, ss = [], 3                          # 3x3 supersampling
    for py in range(size):
        for px in range(size):
            acc = [0.0, 0.0, 0.0, 0.0]
            for sy in range(ss):
                for sx in range(ss):
                    x, y = px + (sx + 0.5) / ss, py + (sy + 0.5) / ss
                    inside = _inside(x, y, poly)
                    d = _edge_distance(x, y, poly)
                    if inside and d > edge:
                        rgb, a = (255, 255, 255), 1.0
                    elif inside or d <= edge * 0.5:
                        rgb, a = (0, 0, 0), 1.0
                    elif d <= ring:
                        rgb, a = RED, 1.0
                    else:
                        continue
                    for i in range(3):
                        acc[i] += rgb[i] * a
                    acc[3] += a
            n = ss * ss
            a = acc[3] / n
            r, g, b = (int(round(acc[i] / n)) for i in range(3))   # premultiplied by coverage
            pixels.append((int(round(a * 255)) << 24) | (r << 16) | (g << 8) | b)
    return pixels, (int(round(pad)), int(round(pad)))


def xcursor(images):
    """Xcursor file: header, TOC, image chunks (type 0xfffd0002)."""
    header = struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(images))
    toc, chunks, offset = b"", b"", 16 + 12 * len(images)
    for size, (pixels, (hx, hy)) in images:
        chunk = struct.pack("<IIIIIIIII", 36, 0xFFFD0002, size, 1, size, size, hx, hy, 0)
        chunk += struct.pack(f"<{len(pixels)}I", *pixels)
        toc += struct.pack("<III", 0xFFFD0002, size, offset)
        chunks += chunk
        offset += len(chunk)
    return header + toc + chunks


def main():
    cursors = OUT / "cursors"
    cursors.mkdir(parents=True, exist_ok=True)
    (cursors / "left_ptr").write_bytes(xcursor([(s, render(s)) for s in SIZES]))
    for alias in ALIASES:
        link = cursors / alias
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to("left_ptr")
    (OUT / "index.theme").write_text(
        "[Icon Theme]\nName=t2-highvis\nComment=Large white arrow with a red outline (t2-mac-kde)\n"
        "Inherits=breeze_cursors\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
