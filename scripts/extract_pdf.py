#!/usr/bin/env python3
"""Extract text per page and the table of contents from a PDF.

Usage:
  python extract_pdf.py input.pdf --out working/deck.json
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    print("Missing dependency: pip install pymupdf", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--no-toc", action="store_true")
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"File not found: {args.pdf}", file=sys.stderr)
        return 2

    doc = pymupdf.open(args.pdf)
    pages = []
    for i, page in enumerate(doc, 1):
        text = page.get_text().strip()
        pages.append({"page": i, "text": text})

    toc = [] if args.no_toc else [
        {"level": level, "title": title, "page": page}
        for level, title, page in doc.get_toc()
    ]

    data = {
        "file": args.pdf.name,
        "pages": pages,
        "toc": toc,
        "page_count": len(pages),
    }

    out = args.out or args.pdf.with_suffix(".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    empty = [p["page"] for p in pages if len(p["text"]) < 30]
    total_chars = sum(len(p["text"]) for p in pages)
    print(f"pages={len(pages)} chars={total_chars} toc={len(toc)}")
    print(f"near_empty_pages={empty[:20]}{' ...' if len(empty) > 20 else ''}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
