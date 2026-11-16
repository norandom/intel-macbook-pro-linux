#!/usr/bin/env python3
"""Render the benchmark charts for docs/benchmark.md from the JSON results (stdlib only).

    python3 tools/benchmark-charts.py            # writes docs/img/bench-*.svg

Charts (light and dark via prefers-color-scheme inside each SVG):
  bench-os.svg           Linux vs macOS on the same Mac, per test, log scale around 1x
  bench-mitigations.svg  Linux with mitigations off vs on, change per test
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "benchmarks"
OUT = ROOT / "docs/img"

TESTS = [  # key, label, group
    ("sha1", "sha256, one core", "CPU work (user space)"),
    ("shaN", "sha256, all 16 threads", "CPU work (user space)"),
    ("gzip", "gzip -6, one core", "CPU work (user space)"),
    ("perl", "perl integer loop *", "CPU work (user space)"),
    ("syscall", "tiny system calls", "OS work (kernel)"),
    ("stat", "file lookup, stat()", "OS work (kernel)"),
    ("spawn", "start a program", "OS work (kernel)"),
    ("fork", "fork a process", "OS work (kernel)"),
    ("pipe", "pipe ping-pong", "OS work (kernel)"),
    ("fault", "fresh memory (page faults)", "OS work (kernel)"),
    ("zero", "kernel zero-fill (dd)", "OS work (kernel)"),
    ("files", "create + delete files **", "OS + filesystem"),
]

STYLE = """<style>
  svg { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --grid:#e4e3df; --a:#2a78d6; --b:#eb6834; --mid:#a3a29c; }
  @media (prefers-color-scheme: dark) {
    svg { --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --grid:#383835; --a:#3987e5; --b:#d95926; --mid:#6f6e69; }
  }
  .bg { fill: var(--surface); } .t { fill: var(--ink); font: 600 15px system-ui, sans-serif; }
  .s { fill: var(--ink2); font: 12px system-ui, sans-serif; } .l { fill: var(--ink); font: 13px system-ui, sans-serif; }
  .g { fill: var(--ink2); font: 600 12px system-ui, sans-serif; } .v { fill: var(--ink); font: 600 12px system-ui, sans-serif; }
  .grid { stroke: var(--grid); stroke-width: 1; } .axis { stroke: var(--ink2); stroke-width: 1.5; }
  .a { fill: var(--a); } .b { fill: var(--b); } .mid { fill: var(--mid); }
</style>"""


def load(path):
    return json.loads(path.read_text())["metrics"]


def spread(m):
    return (m["max"] - m["min"]) / m["median"]


def svg(width, height, body, title, subtitle):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">\n{STYLE}\n'
            f'<rect class="bg" width="{width}" height="{height}" rx="8"/>\n'
            f'<text class="t" x="20" y="28">{title}</text>\n<text class="s" x="20" y="47">{subtitle}</text>\n'
            + "\n".join(body) + "\n</svg>\n")


def rows(top):
    """Yield (y, key, label, new_group) with group headers spaced in."""
    y, group = top, None
    for key, label, g in TESTS:
        if g != group:
            y += 10
            yield y, None, g, True
            y += 22
            group = g
        yield y, key, label, False
        y += 26


def os_chart(linux, macos):
    import math
    W, LX, X0, X1 = 780, 20, 250, 690
    lo, hi = -1, 5  # log2: 0.5x .. 32x
    sx = lambda r: X0 + (math.log2(r) - lo) / (hi - lo) * (X1 - X0)
    body, layout = [], list(rows(70))
    bottom = layout[-1][0] + 20
    for t in (0.5, 1, 2, 4, 8, 16, 32):
        x = sx(t)
        body.append(f'<line class="{"axis" if t == 1 else "grid"}" x1="{x:.1f}" y1="62" x2="{x:.1f}" y2="{bottom}"/>')
        body.append(f'<text class="s" x="{x:.1f}" y="{bottom + 16}" text-anchor="middle">{t:g}×</text>')
    body.append(f'<text class="s" x="{sx(0.5) + 4:.1f}" y="{bottom + 34}">◀ macOS faster</text>')
    body.append(f'<text class="s" x="{X1:.1f}" y="{bottom + 34}" text-anchor="end">Linux faster ▶</text>')
    for y, key, label, header in layout:
        if header:
            body.append(f'<text class="g" x="{LX}" y="{y + 4}">{label.upper()}</text>')
            continue
        r = linux[key]["median"] / macos[key]["median"]
        noise = max(spread(linux[key]), spread(macos[key]))
        cls = "mid" if abs(r - 1) <= max(noise, 0.05) else ("a" if r > 1 else "b")
        x1, x2 = sorted((sx(1), sx(r)))
        body.append(f'<text class="l" x="{LX}" y="{y + 4}">{label}</text>')
        body.append(f'<rect class="{cls}" x="{x1:.1f}" y="{y - 8}" width="{max(x2 - x1, 2):.1f}" height="16" rx="3"/>')
        text = "about equal" if cls == "mid" else (f"{r:.1f}× Linux" if r > 1 else f"{1 / r:.1f}× macOS")
        tx, anchor = (x2 + 6, "start") if r >= 1 else (x1 - 6, "end")
        body.append(f'<text class="v" x="{tx:.1f}" y="{y + 4}" text-anchor="{anchor}">{text}</text>')
    return svg(W, bottom + 50, body, "Same MacBook Pro, two operating systems",
               "How many times faster one OS runs each test (median of 10 runs, turbo off, on AC). Gray: within run-to-run noise.")


def mitigation_chart(on, off):
    W, LX, X0, X1 = 780, 20, 250, 690
    top_pct = 30
    sx = lambda p: X0 + p / top_pct * (X1 - X0)
    body, layout = [], list(rows(70))
    bottom = layout[-1][0] + 20
    for p in range(0, top_pct + 1, 5):
        body.append(f'<line class="{"axis" if p == 0 else "grid"}" x1="{sx(p):.1f}" y1="62" x2="{sx(p):.1f}" y2="{bottom}"/>')
        body.append(f'<text class="s" x="{sx(p):.1f}" y="{bottom + 16}" text-anchor="middle">+{p} %</text>')
    for y, key, label, header in layout:
        if header:
            body.append(f'<text class="g" x="{LX}" y="{y + 4}">{label.upper()}</text>')
            continue
        gain = (off[key]["median"] / on[key]["median"] - 1) * 100
        noise = max(spread(on[key]), spread(off[key])) * 100
        cls = "a" if gain > noise and gain >= 2 else "mid"
        w = max(sx(max(gain, 0)) - X0, 2)
        body.append(f'<text class="l" x="{LX}" y="{y + 4}">{label}</text>')
        body.append(f'<rect class="{cls}" x="{X0}" y="{y - 8}" width="{w:.1f}" height="16" rx="3"/>')
        text = ("0 %" if round(gain) == 0 else f"{gain:+.0f} %") + ("" if cls == "a" else " (noise)")
        body.append(f'<text class="v" x="{X0 + w + 6:.1f}" y="{y + 4}">{text}</text>')
    return svg(W, bottom + 34, body, "What switching the CPU mitigations off bought",
               "Linux, same Mac, mitigations off vs on (median of 10 runs each). Gray: smaller than run-to-run noise.")


def main():
    linux, macos = load(B / "linux.json"), load(B / "macos.json")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "bench-os.svg").write_text(os_chart(linux, macos))
    off_path = B / "mitigations-off/linux.json"
    if off_path.exists():
        (OUT / "bench-mitigations.svg").write_text(mitigation_chart(linux, load(off_path)))
    print("written:", ", ".join(p.name for p in sorted(OUT.glob("bench-*.svg"))))


if __name__ == "__main__":
    main()
