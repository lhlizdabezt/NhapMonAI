from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "alpr-pipeline-motion.gif"
WIDTH, HEIGHT = 900, 300
FRAMES = 32
DURATION_MS = 85


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size=size)


TITLE = font(28, True)
SUBTITLE = font(15)
CARD_TITLE = font(22, True)
CARD_SMALL = font(13)
CAPTION = font(14)
VALUE = font(22, True)


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw: ImageDraw.ImageDraw, box, text, fnt, fill):
    left, top, right, bottom = box
    bbox = draw.textbbox((0, 0), text, font=fnt)
    x = left + (right - left - (bbox[2] - bbox[0])) / 2
    y = top + (bottom - top - (bbox[3] - bbox[1])) / 2 - 1
    draw.text((x, y), text, font=fnt, fill=fill)


def add_card(draw, x, y, w, h, label, small, color, phase):
    lift = int(4 * math.sin(phase))
    glow = int(40 + 28 * (math.sin(phase) + 1))
    shadow = (0, 0, 0, 80)
    rounded(draw, (x + 4, y + 8 + lift, x + w + 4, y + h + 8 + lift), 22, shadow)
    rounded(draw, (x, y + lift, x + w, y + h + lift), 22, (17, 24, 39, 245), (color[0], color[1], color[2], 190), 2)
    rounded(draw, (x + 16, y + 18 + lift, x + w - 16, y + 54 + lift), 16, (color[0], color[1], color[2], glow))
    centered(draw, (x + 18, y + 16 + lift, x + w - 18, y + 58 + lift), label, CARD_TITLE, (248, 250, 252, 255))
    centered(draw, (x + 12, y + 66 + lift, x + w - 12, y + h - 14 + lift), small, CARD_SMALL, (203, 213, 225, 255))


def make_frame(index: int) -> Image.Image:
    phase = (index / FRAMES) * math.tau
    img = Image.new("RGBA", (WIDTH, HEIGHT), (8, 13, 25, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    for y in range(HEIGHT):
        mix = y / HEIGHT
        r = int(10 + 8 * mix)
        g = int(18 + 52 * mix)
        b = int(36 + 50 * mix)
        draw.line((0, y, WIDTH, y), fill=(r, g, b, 255))

    rounded(draw, (22, 22, WIDTH - 22, HEIGHT - 22), 26, (15, 23, 42, 210), (56, 189, 248, 65), 1)
    draw.text((42, 38), "NhapMonAI - Vietnamese License Plate Recognition", font=TITLE, fill=(241, 245, 249, 255))
    draw.text((43, 74), "Line-free ALPR evidence: detector, OCR, desktop app and LAN gate prototype", font=SUBTITLE, fill=(186, 230, 253, 255))

    cards = [
        (44, 112, 166, 82, "Input", "image or video", (59, 130, 246), phase),
        (256, 112, 166, 82, "YOLO", "plate detector", (20, 184, 166), phase + 0.8),
        (478, 112, 166, 82, "OCR", "text cleanup", (249, 115, 22), phase + 1.6),
        (690, 112, 166, 82, "Gate", "allow-list demo", (168, 85, 247), phase + 2.4),
    ]
    for args in cards:
        add_card(draw, *args)

    rounded(draw, (346, 222, 556, 266), 12, (226, 232, 240, 255), (59, 130, 246, 220), 2)
    rounded(draw, (356, 231, 386, 257), 4, (37, 99, 235, 255))
    draw.text((398, 231), "59A-222.56", font=VALUE, fill=(15, 23, 42, 255))
    draw.text((44, 238), "Validation mAP50: 0.99450", font=CAPTION, fill=(203, 213, 225, 255))
    draw.text((648, 238), "Output: annotated media and CSV", font=CAPTION, fill=(203, 213, 225, 255))
    return img.convert("P", palette=Image.Palette.ADAPTIVE)


def main() -> None:
    frames = [make_frame(i) for i in range(FRAMES)]
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_MS,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
