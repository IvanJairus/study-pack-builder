#!/usr/bin/env python3
"""Extract multiple-choice questions and highlighted answers from a PDF.

Default conventions:
  yellow fill  = correct option
  green fill   = explanatory note
Review every question flagged as missing or ambiguous.

Usage:
  python extract_questions.py answer-key.pdf --out working/questions.json
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    print("Missing dependency: pip install pymupdf", file=sys.stderr)
    raise SystemExit(2)


def is_yellow(color):
    if not color or len(color) < 3:
        return False
    r, g, b = color[:3]
    return r > 0.85 and g > 0.85 and b < 0.25


def is_green(color):
    if not color or len(color) < 3:
        return False
    r, g, b = color[:3]
    return g > 0.6 and r < 0.5 and b < 0.5 and g > r + 0.2


def highlight_ratio(page, rect, predicate):
    total = 0.0
    for drawing in page.get_drawings():
        fill = drawing.get("fill")
        if predicate(fill):
            overlap = rect & drawing["rect"]
            if not overlap.is_empty:
                total += overlap.get_area()
    return total / (rect.get_area() or 1)


def page_lines(page):
    lines = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = line["spans"]
            text = "".join(span["text"] for span in spans).strip()
            if not text:
                continue
            italic = " ".join(span["text"] for span in spans if span["flags"] & 2).strip()
            rect = pymupdf.Rect(line["bbox"])
            lines.append(
                {
                    "text": text,
                    "italic": italic,
                    "x": rect.x0,
                    "y": rect.y0,
                    "yellow": highlight_ratio(page, rect, is_yellow),
                    "green": highlight_ratio(page, rect, is_green),
                }
            )
    lines.sort(key=lambda item: (round(item["y"] / 3), item["x"]))
    return lines


def clean(value):
    value = re.sub(r"\s+", " ", value).strip()
    value = value.replace(" - ", " ")
    return value


def parse_pdf(path: Path):
    doc = pymupdf.open(path)
    lines = []
    for page in doc:
        for line in page_lines(page):
            line["page"] = page.number + 1
            lines.append(line)

    questions = []
    current = None
    section = None
    last_option = None

    for line in lines:
        text = line["text"]

        if re.match(r"^[A-Z]\.\s+[A-Z][A-Z0-9\s\-/&]+$", text) and len(text) < 110:
            section = clean(text)
            continue

        start = re.match(r"^(\d{1,3})[.)]\s+(.*)$", text)
        if start and len(text) > 10 and int(start.group(1)) <= 250:
            if current:
                questions.append(current)
            current = {
                "no": int(start.group(1)),
                "section": section,
                "stem": [start.group(2)],
                "options": {},
                "order": [],
                "option_lines": {},
                "notes": [],
                "page": line["page"],
            }
            last_option = None
            continue

        if current is None:
            continue

        option = re.match(r"^([A-D])[.)]\s*(.*)$", text)
        if option:
            key = option.group(1)
            if key not in current["options"]:
                current["options"][key] = []
                current["option_lines"][key] = []
                current["order"].append(key)
            current["options"][key].append(option.group(2))
            current["option_lines"][key].append(line["yellow"])
            last_option = key
            if line["italic"] and line["italic"] not in text:
                current["notes"].append({"option": key, "text": clean(line["italic"])})
            continue

        if re.match(r"^(note|catatan|keterangan)\s*:", text, re.I):
            current["notes"].append({"option": last_option, "text": clean(text)})
            continue

        if line["green"] > 0.15 or (line["italic"] and not text.startswith(("A.", "B.", "C.", "D."))):
            current["notes"].append({"option": last_option, "text": clean(line["italic"] or text)})
            continue

        if last_option:
            current["options"][last_option].append(text)
            current["option_lines"][last_option].append(line["yellow"])
        else:
            current["stem"].append(text)

    if current:
        questions.append(current)

    for question in questions:
        scores = {
            key: sum(question["option_lines"][key]) for key in question["order"]
        }
        ranked = sorted(scores.items(), key=lambda item: -item[1])
        question["answer"] = ranked[0][0] if ranked and ranked[0][1] >= 0.15 else None
        question["ambiguous"] = sum(1 for score in scores.values() if score >= 0.15) > 1
        question["stem"] = clean(" ".join(question["stem"]))
        question["options"] = {
            key: clean(" ".join(values)) for key, values in question["options"].items()
        }
        question.pop("option_lines", None)

    return {
        "file": path.name,
        "questions": questions,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"File not found: {args.pdf}", file=sys.stderr)
        return 2

    data = parse_pdf(args.pdf)
    data["set"] = args.pdf.stem
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    missing = [q["no"] for q in data["questions"] if not q["answer"]]
    ambiguous = [q["no"] for q in data["questions"] if q["ambiguous"]]
    print(f"questions={len(data['questions'])} missing={missing} ambiguous={ambiguous}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
