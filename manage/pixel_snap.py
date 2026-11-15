"""Snap Hyprland sizes to whole physical pixels at a fractional monitor scale.

At scale 1.6 a 2 px border is 3.2 device pixels and a 22 px title bar 35.2: those edges
round differently on every repaint (video), which shows as a flickering line.
"""
from fractions import Fraction


def snap(value: int, scale) -> int:
    """Nearest logical size whose device size is an integer (ties: the smaller one)."""
    s = Fraction(str(scale))
    best = None
    for v in range(0, value * 3 + 3):
        if (v * s).denominator == 1:
            key = (abs(v - value), v)
            best = key if best is None or key < best else best
    return best[1] if best else value


def conf(scale, border: int = 2, bar_height: int = 22) -> str:
    if str(scale) == "auto" or Fraction(str(scale)).denominator == 1:
        return "# integer or auto scale: no snapping needed\n"
    return ("general {\n"
            f"    border_size = {snap(border, scale)}\n"
            "}\n"
            "plugin {\n    hyprbars {\n"
            f"        bar_height = {snap(bar_height, scale)}\n"
            "    }\n}\n")
