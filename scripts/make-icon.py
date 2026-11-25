"""Generate the PyDoctor icons.

The mark is a stethoscope wrapped around a Python snake. Two accent variants
are produced so the React app and the Tkinter fallback are distinguishable:

- ``icon-ui.*``: cyan accent, used by ``PyDoctor-UI.exe`` and the React header.
- ``icon-tk.*``: amber accent, used by ``PyDoctor.exe``.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

SIZE = 1024
WHITE = (232, 241, 250, 255)
BLUE = (55, 118, 171, 255)
YELLOW = (255, 212, 59, 255)
NAVY = (10, 16, 28, 255)
TOP = (27, 42, 74)
BOTTOM = (8, 13, 24)
BORDER = (42, 59, 92, 255)
ACCENTS = {"ui": (34, 211, 238, 255), "tk": (251, 191, 36, 255)}


def _bezier(p0, p1, p2, p3, steps=240):
    points = []
    for index in range(steps + 1):
        t = index / steps
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points


def _gradient() -> Image.Image:
    gradient = Image.new("RGBA", (SIZE, SIZE))
    draw = ImageDraw.Draw(gradient)
    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = tuple(int(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        draw.line([(0, y), (SIZE, y)], fill=color + (255,))
    return gradient


def _render(accent: tuple[int, int, int, int]) -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((32, 32, 992, 992), radius=200, fill=255)
    image.paste(_gradient(), (0, 0), mask)

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((32, 32, 992, 992), radius=200, outline=BORDER, width=12)

    tube = _bezier((285, 388), (285, 900), (739, 900), (739, 388))
    snake = [(440, 400), (580, 400), (580, 520), (440, 520), (440, 640), (580, 640)]

    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.line(snake, fill=(55, 118, 171, 150), width=170, joint="curve")
    glow_draw.ellipse((360, 320, 520, 480), fill=(255, 212, 59, 90))
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(46)))

    draw = ImageDraw.Draw(image)
    draw.line(tube, fill=WHITE, width=56, joint="curve")
    for point in (tube[0], tube[-1]):
        draw.ellipse(
            (point[0] - 28, point[1] - 28, point[0] + 28, point[1] + 28), fill=WHITE
        )

    for start, end in (((285, 388), (330, 300)), ((739, 388), (694, 300))):
        draw.line([start, end], fill=WHITE, width=56)
        draw.ellipse(
            (end[0] - 28, end[1] - 28, end[0] + 28, end[1] + 28), fill=WHITE
        )

    draw.ellipse((420, 708, 604, 892), fill=WHITE)
    draw.ellipse((442, 730, 582, 870), outline=accent, width=10)
    draw.ellipse((460, 748, 564, 852), fill=NAVY)
    draw.rectangle((504, 772, 520, 828), fill=WHITE)
    draw.rectangle((476, 796, 548, 812), fill=WHITE)

    draw.line(snake, fill=BLUE, width=104, joint="curve")
    for point in (snake[0], snake[-1]):
        draw.ellipse(
            (point[0] - 52, point[1] - 52, point[0] + 52, point[1] + 52), fill=BLUE
        )
    draw.line(snake, fill=(90, 160, 215, 255), width=30, joint="curve")

    draw.ellipse((360, 320, 520, 480), fill=YELLOW)
    draw.ellipse((405, 375, 423, 393), fill=NAVY)
    draw.ellipse((457, 375, 475, 393), fill=NAVY)
    return image


def _svg(accent: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" role="img" aria-label="PyDoctor">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#1b2a4a"/>
      <stop offset="1" stop-color="#080d18"/>
    </linearGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="26"/>
    </filter>
  </defs>
  <rect x="32" y="32" width="960" height="960" rx="200" fill="url(#bg)" stroke="#2a3b5c" stroke-width="12"/>
  <polyline points="440,400 580,400 580,520 440,520 440,640 580,640" fill="none" stroke="#3776ab" stroke-width="150" stroke-linecap="round" stroke-linejoin="round" opacity="0.5" filter="url(#glow)"/>
  <path d="M285 388 C285 900 739 900 739 388" fill="none" stroke="#e8f1fa" stroke-width="56" stroke-linecap="round"/>
  <path d="M285 388 L330 300" fill="none" stroke="#e8f1fa" stroke-width="56" stroke-linecap="round"/>
  <path d="M739 388 L694 300" fill="none" stroke="#e8f1fa" stroke-width="56" stroke-linecap="round"/>
  <circle cx="330" cy="300" r="28" fill="#e8f1fa"/>
  <circle cx="694" cy="300" r="28" fill="#e8f1fa"/>
  <circle cx="512" cy="800" r="92" fill="#e8f1fa"/>
  <circle cx="512" cy="800" r="70" fill="none" stroke="{accent}" stroke-width="10"/>
  <circle cx="512" cy="800" r="52" fill="#0a101c"/>
  <rect x="504" y="772" width="16" height="56" rx="4" fill="#e8f1fa"/>
  <rect x="476" y="796" width="72" height="16" rx="4" fill="#e8f1fa"/>
  <polyline points="440,400 580,400 580,520 440,520 440,640 580,640" fill="none" stroke="#3776ab" stroke-width="104" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="440,400 580,400 580,520 440,520 440,640 580,640" fill="none" stroke="#5aa0d7" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="440" cy="400" r="80" fill="#ffd43b"/>
  <circle cx="414" cy="384" r="9" fill="#0a101c"/>
  <circle cx="466" cy="384" r="9" fill="#0a101c"/>
</svg>
"""


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    for name, accent in ACCENTS.items():
        image = _render(accent)
        image.save(ASSETS / f"icon-{name}.ico", format="ICO", sizes=sizes)
        if name == "ui":
            image.save(ASSETS / "icon.ico", format="ICO", sizes=sizes)
            image.resize((256, 256), Image.LANCZOS).save(ASSETS / "icon-256.png")
            (ASSETS / "icon.svg").write_text(_svg("#22d3ee"), encoding="utf-8")
    print(f"Wrote icons to {ASSETS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
