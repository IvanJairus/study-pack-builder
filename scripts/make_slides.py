#!/usr/bin/env python3
"""Create 1920x1080 white-theme slides from a video script and screenshots.

Usage:
  python make_slides.py working/script-timed.json --shots working/shots --out working/slides
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
except ImportError:
    print("Missing dependency: pip install pillow", file=sys.stderr)
    raise SystemExit(2)

W, H = 1920, 1080
INK = (18, 19, 22)
MUTED = (98, 106, 115)
FAINT = (138, 145, 154)
LINE = (228, 231, 234)

FONT_CANDIDATES = {
    "bold": [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "regular": [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}


def load_font(kind, size):
    for path in FONT_CANDIDATES[kind]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def wrap(draw, text, font, width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textlength(candidate, font=font) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_title(draw, text, width, max_height=300):
    for size in (72, 68, 64, 60, 56, 52):
        font = load_font("bold", size)
        lines = wrap(draw, text, font, width)
        line_height = int(size * 1.12)
        if len(lines) * line_height <= max_height:
            return font, lines, line_height
    font = load_font("bold", 52)
    return font, wrap(draw, text, font, width), int(52 * 1.12)


def background():
    image = Image.new("RGB", (1, H))
    top, bottom = (255, 255, 255), (247, 248, 250)
    for y in range(H):
        ratio = y / (H - 1)
        image.putpixel((0, y), tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3)))
    return image.resize((W, H))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("script", type=Path)
    ap.add_argument("--shots", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    data = json.loads(args.script.read_text(encoding="utf-8"))
    sections = data.get("sections") if isinstance(data, dict) else data
    if not isinstance(sections, list) or not sections:
        print("Script must contain a non-empty sections list", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    total = len(sections)
    for index, section in enumerate(sections, 1):
        color = rgb(section.get("color", "#2f5d4f"))
        image = background()
        draw = ImageDraw.Draw(image)
        for x in range(0, W, 80):
            draw.line([(x, 0), (x, H)], fill=(239, 241, 244), width=1)
        for y in range(0, H, 80):
            draw.line([(0, y), (W, y)], fill=(239, 241, 244), width=1)
        draw.rectangle([0, 0, 7, H], fill=color)

        draw.text((110, 82), f"BAGIAN {section.get('num', index):0>2}  ·  {section.get('kicker', '')}  ·  STUDY PACK", font=load_font("bold", 21), fill=color)
        title_font, title_lines, line_height = fit_title(draw, section.get("title", ""), 760)
        y = 135
        for line in title_lines:
            draw.text((110, y), line, font=title_font, fill=INK)
            y += line_height
        draw.rectangle([110, y + 22, 210, y + 27], fill=color)
        y += 58

        bullet_font = load_font("regular", 30)
        for bullet in section.get("bullets", []):
            lines = wrap(draw, bullet, bullet_font, 740)
            draw.rectangle([112, y + 13, 122, y + 23], fill=color)
            for offset, line in enumerate(lines):
                draw.text((140, y + offset * 42), line, font=bullet_font, fill=(52, 56, 62))
            y += max(44, len(lines) * 42 + 14)

        draw.line([(110, 810), (1810, 810)], fill=LINE, width=1)
        draw.text((110, 835), "INTI", font=load_font("bold", 18), fill=color)
        takeaway_font = load_font("regular", 27)
        takeaway_lines = wrap(draw, section.get("takeaway", ""), takeaway_font, 1560)
        takeaway_y = 866
        for line in takeaway_lines[:2]:
            draw.text((110, takeaway_y), line, font=takeaway_font, fill=(52, 56, 62))
            takeaway_y += 37

        label = f"DETAIL  ·  {section.get('page', '')}"
        label_font = load_font("bold", 18)
        label_width = draw.textlength(label, font=label_font)
        draw.rounded_rectangle([110, 946, 110 + label_width + 42, 988], radius=21, fill=color)
        draw.text((131, 957), label, font=label_font, fill=(255, 255, 255))

        shot_path = args.shots / section.get("shot", "")
        if shot_path.exists():
            shot = Image.open(shot_path).convert("RGB")
            card_x, card_y, card_w, card_h = 960, 160, 840, 505
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rounded_rectangle([card_x + 8, card_y + 12, card_x + card_w + 8, card_y + card_h + 12], radius=10, fill=(18, 19, 22, 36))
            shadow = shadow.filter(ImageFilter.GaussianBlur(12))
            image = Image.alpha_composite(image.convert("RGBA"), shadow).convert("RGB")
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=8, fill=(255, 255, 255), outline=(228, 231, 234), width=1)
            draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + 32], radius=8, fill=(242, 244, 246))
            draw.rectangle([card_x, card_y + 22, card_x + card_w, card_y + 32], fill=(242, 244, 246))
            for dot in range(3):
                draw.ellipse([card_x + 16 + dot * 18, card_y + 12, card_x + 24 + dot * 18, card_y + 20], fill=(200, 206, 213))
            draw.text((card_x + 76, card_y + 9), "study-pack  ·  page preview", font=load_font("regular", 16), fill=MUTED)
            shot = ImageOps.fit(shot, (card_w - 2, card_h - 34), method=Image.LANCZOS, centering=(0.5, 0.12))
            image.paste(shot, (card_x + 1, card_y + 33))
            draw.rectangle([card_x + 1, card_y + 33, card_x + card_w - 1, card_y + card_h - 1], outline=(228, 231, 234), width=1)
            draw.text((card_x, card_y + card_h + 20), section.get("page", ""), font=load_font("regular", 18), fill=FAINT)

        draw.line([(110, 1012), (1810, 1012)], fill=LINE, width=1)
        draw.text((110, 1032), "Study Pack Builder  ·  2026", font=load_font("regular", 17), fill=FAINT)
        draw.text((1660, 1032), f"{index:02d} / {total:02d}", font=load_font("bold", 17), fill=FAINT)
        draw.rounded_rectangle([110, 1062, 1810, 1068], radius=3, fill=(232, 235, 239))
        draw.rounded_rectangle([110, 1062, 110 + int(1700 * index / total), 1068], radius=3, fill=color)

        out = args.out / f"{section.get('num', index):0>2}-{section['id']}.png"
        image.save(out)
        print(f"wrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
