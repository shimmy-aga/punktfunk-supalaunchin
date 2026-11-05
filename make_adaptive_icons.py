#!/usr/bin/env python3
"""Generate adaptive icons (background + foreground + monochrome) and the
legacy PNG fallback / TV banner for the two shortcut APKs.

Needs ImageMagick (`magick`), Pillow, and the Liberation Sans fonts.
The source SVGs live in ./assets; the generated resources land in
./steam/res and ./homelab/res.
"""
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "assets"
FONT_BOLD = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"

APPS = {
    "steam": {
        "svg": SRC / "steam.svg",
        "bg": "#1B2838",
        "top": (23, 26, 33),
        "bottom": (27, 40, 56),
        "line1": "Steam BPM",
        "line2": "Desktop",
    },
    "homelab": {
        "svg": SRC / "bazzite.svg",
        "bg": "#1478DB",
        "top": (16, 78, 160),
        "bottom": (24, 120, 215),
        "line1": "Gamescope",
        "line2": "Game Mode",
    },
}


def svg_path(svg: Path):
    text = svg.read_text()
    vb = re.search(r'viewBox="([^"]+)"', text)
    if not vb:
        raise SystemExit(f"no viewBox in {svg}")
    x, y, w, h = (float(v) for v in vb.group(1).replace(",", " ").split())
    paths = re.findall(r'<path[^>]*\sd="([^"]+)"', text)
    if not paths:
        raise SystemExit(f"no path in {svg}")
    return paths[0], (x, y, w, h)


def vector(path_data: str, view: tuple[float, float, float, float], fill: str) -> str:
    vx, vy, vw, vh = view
    safe = 66.0
    scale = safe / max(vw, vh)
    tx = (108.0 - vw * scale) / 2.0 - vx * scale
    ty = (108.0 - vh * scale) / 2.0 - vy * scale
    return f'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <group
        android:scaleX="{scale:.6f}"
        android:scaleY="{scale:.6f}"
        android:translateX="{tx:.6f}"
        android:translateY="{ty:.6f}">
        <path
            android:fillColor="{fill}"
            android:pathData="{path_data}" />
    </group>
</vector>
'''


def gradient(size, top, bottom):
    w, h = size
    im = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        d.point((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return im.resize((w, h))


def glyph(svg: Path, px: int) -> Image.Image:
    out = ROOT / (svg.stem + "-adaptive-raw.png")
    subprocess.run(
        ["magick", "-background", "none", "-density", "600",
         str(svg), "-resize", f"{px}x{px}", str(out)],
        check=True,
    )
    im = Image.open(out).convert("RGBA")
    white = Image.new("RGBA", im.size, (255, 255, 255, 0))
    white.putalpha(im.getchannel("A"))
    return white


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main():
    for name, cfg in APPS.items():
        proj = ROOT / name
        res = proj / "res"
        path_data, view = svg_path(cfg["svg"])

        write_text(res / "values/colors.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">{cfg["bg"]}</color>
</resources>
''')
        write_text(res / "drawable/ic_launcher_foreground.xml",
                   vector(path_data, view, "#FFFFFF"))
        write_text(res / "drawable/ic_launcher_monochrome.xml",
                   vector(path_data, view, "#000000"))
        adaptive = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
    <monochrome android:drawable="@drawable/ic_launcher_monochrome" />
</adaptive-icon>
'''
        write_text(res / "mipmap-anydpi-v26/ic_launcher.xml", adaptive)
        write_text(res / "mipmap-anydpi-v26/ic_launcher_round.xml", adaptive)

        g = glyph(cfg["svg"], 1024)
        size = 512
        bg = gradient((size, size), cfg["top"], cfg["bottom"]).convert("RGBA")
        bg.putalpha(rounded_mask((size, size), 112))
        target = 440
        g = g.resize((target, target), Image.LANCZOS)
        bg.alpha_composite(g, ((size - target) // 2, (size - target) // 2))
        out = res / "mipmap-xxxhdpi/ic_launcher.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        bg.save(out)
        bg.save(res / "mipmap-xxxhdpi/ic_launcher_round.png")

        canvas = gradient((320, 180), cfg["top"], cfg["bottom"]).convert("RGBA")
        icon = g.resize((104, 104), Image.LANCZOS)
        canvas.alpha_composite(icon, (24, (180 - 104) // 2))
        d = ImageDraw.Draw(canvas)
        f1 = ImageFont.truetype(FONT_BOLD, 30)
        f2 = ImageFont.truetype(FONT_REG, 19)
        d.text((146, 66), cfg["line1"], font=f1, fill=(255, 255, 255, 255))
        d.text((146, 101), cfg["line2"], font=f2, fill=(210, 226, 245, 255))
        canvas.convert("RGB").save(res / "drawable/banner.png")

        print(f"{name}: adaptive icon + legacy PNG + banner")


if __name__ == "__main__":
    main()
