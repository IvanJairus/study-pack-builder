#!/usr/bin/env python3
"""Generate assets/abbreviations.js from the visible abbreviation table.

The table in reference.html is the single source of truth. Tooltips and the
reference search both read the generated file.

Usage:
  python build_abbreviations.py
  python build_abbreviations.py --reference assets/site-template/reference.html --out assets/site-template/assets/abbreviations.js
  python build_abbreviations.py --check
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

ROW = re.compile(r"<tr\b[^>]*\bdata-abbr-row\b[^>]*>(.*?)</tr>", re.S | re.I)
CELL = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")


def text_of(markup):
    value = TAG.sub(" ", markup)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def short_expansion(value):
    value = re.sub(r"\s+", " ", value).strip()
    match = re.match(r"(.+?[.!?])(?:\s|$)", value)
    if match:
        value = match.group(1).rstrip(".")
    if len(value) > 140:
        value = value[:137].rstrip() + "..."
    return value


def read_rows(reference):
    markup = reference.read_text(encoding="utf-8")
    rows = []
    errors = []
    for row_match in ROW.finditer(markup):
        cells = [text_of(cell) for cell in CELL.findall(row_match.group(1))]
        if len(cells) < 2:
            errors.append("abbreviation row needs a short form and an expansion")
            continue
        key = cells[0].strip()
        expansion = short_expansion(cells[1])
        context = cells[2].strip() if len(cells) > 2 else ""
        if not key or not expansion:
            errors.append(f"incomplete abbreviation row: {cells}")
            continue
        if any(character.isdigit() for character in key) or len(key) > 24:
            continue
        rows.append({"key": key, "expansion": expansion, "context": context})
    if not rows:
        errors.append(f"no data-abbr-row entries found in {reference}")
    seen = set()
    for row in rows:
        if row["key"] in seen:
            errors.append(f"duplicate abbreviation: {row['key']}")
        seen.add(row["key"])
    return rows, errors


def render(rows):
    data = {
        row["key"]: {"expansion": row["expansion"], "context": row["context"]}
        for row in sorted(rows, key=lambda item: item["key"].lower())
    }
    body = json.dumps(data, ensure_ascii=False, indent=2)
    return (
        "// Generated from reference.html. Edit the abbreviation table, then run scripts/build_abbreviations.py.\n"
        "window.ABBREVIATIONS = " + body + ";\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reference", type=Path, default=Path("assets/site-template/reference.html"))
    parser.add_argument("--out", type=Path, default=Path("assets/site-template/assets/abbreviations.js"))
    parser.add_argument("--check", action="store_true", help="Fail when the generated file is out of date")
    args = parser.parse_args()

    if not args.reference.exists():
        print(f"Reference not found: {args.reference}", file=sys.stderr)
        return 2
    rows, errors = read_rows(args.reference)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    content = render(rows)
    if args.check:
        if not args.out.exists():
            print(f"missing generated file: {args.out}", file=sys.stderr)
            return 1
        current = args.out.read_text(encoding="utf-8")
        if current != content:
            print(f"out of date: {args.out}; run scripts/build_abbreviations.py", file=sys.stderr)
            return 1
        print(f"abbreviations: {len(rows)} terms, up to date")
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(content, encoding="utf-8")
    print(f"abbreviations={len(rows)}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
