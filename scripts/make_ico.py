#!/usr/bin/env python3
"""Generate src/bertytype/assets/icon.ico from the waveform design."""
from pathlib import Path
from PIL import Image, ImageDraw

_BAR_HEIGHTS_64 = [16, 32, 48, 32, 16]
_ICON_COLOR = "#4CAF50"
_OUT = Path(__file__).parent.parent / "src" / "bertytype" / "assets" / "icon.ico"


def _make_icon_at_size(size: int) -> Image.Image:
    scale = size / 64
    bar_w = max(1, round(8 * scale))
    bar_gap = max(1, round(4 * scale))
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    total_width = len(_BAR_HEIGHTS_64) * bar_w + (len(_BAR_HEIGHTS_64) - 1) * bar_gap
    x_start = (size - total_width) // 2
    for i, bar_h_64 in enumerate(_BAR_HEIGHTS_64):
        bar_h = max(1, round(bar_h_64 * scale))
        x = x_start + i * (bar_w + bar_gap)
        y_top = (size - bar_h) // 2
        draw.rounded_rectangle(
            [x, y_top, x + bar_w, y_top + bar_h],
            radius=max(1, round(2 * scale)),
            fill=_ICON_COLOR,
        )
    return img


if __name__ == "__main__":
    sizes = [16, 32, 48, 256]
    icons = [_make_icon_at_size(s) for s in sizes]
    icons[0].save(_OUT, format="ICO", sizes=[(s, s) for s in sizes], append_images=icons[1:])
    print(f"Created {_OUT}  ({', '.join(str(s) for s in sizes)}px)")
