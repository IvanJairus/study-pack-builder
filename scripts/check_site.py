#!/usr/bin/env python3
"""Check a generated study pack: links, quiz data, PDF count, and artifacts.

Usage:
  python check_site.py --root output --quiz output/assets/js/quiz-data.js --pdf output/bank-soal/question-bank.pdf
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

SKIP_PREFIXES = ("http://", "https://", "#", "mailto:", "tel:", "javascript:", "data:")
CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")


def html_files(root: Path):
    return sorted(root.rglob("*.html"))


def check_links(root: Path):
    broken = []
    for file in html_files(root):
        text = file.read_text(encoding="utf-8", errors="ignore")
        for raw in re.findall(r'(?:href|src)="([^"]+)"', text):
            if raw.startswith(SKIP_PREFIXES):
                continue
            target = raw.split("#")[0].split("?")[0]
            if not target:
                continue
            path = (file.parent / target).resolve()
            if not path.exists():
                broken.append((str(file.relative_to(root)), raw))
    return broken


def check_quiz(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"window\.QUIZ_DATA\s*=\s*(\[.*\])\s*;", text, re.S)
    if not match:
        return ["quiz data not found"], 0, 0
    try:
        data = json.loads(match.group(1))
    except Exception as exc:
        return [f"quiz data is not valid JSON: {exc}"], 0, 0
    errors = []
    ids = set()
    topics = set()
    for index, question in enumerate(data, 1):
        qid = question.get("id", f"#{index}")
        if qid in ids:
            errors.append(f"duplicate id {qid}")
        ids.add(qid)
        if question.get("topic"):
            topics.add(question["topic"])
        options = question.get("options", {})
        if not isinstance(options, dict) or len(options) != 4:
            errors.append(f"{qid}: expected 4 options")
        if question.get("answer") not in options:
            errors.append(f"{qid}: answer not in options")
        for field in ("question", "explanation", "trap"):
            if not str(question.get(field, "")).strip():
                errors.append(f"{qid}: empty {field}")
    return errors, len(data), len(topics)


def check_pdf(path: Path, expected: int | None):
    try:
        import pymupdf
    except ImportError:
        return ["pymupdf not installed; cannot check PDF"], 0
    doc = pymupdf.open(path)
    text = "".join(page.get_text() for page in doc)
    ids = set(re.findall(r"\bQ\d+\b", text))
    errors = []
    if expected is not None and len(ids) != expected:
        errors.append(f"PDF has {len(ids)} question IDs, expected {expected}")
    return errors, len(ids)


def check_artifacts(root: Path):
    issues = []
    for suffix in ("*.html", "*.js", "*.css", "*.md"):
        for file in root.rglob(suffix):
            text = file.read_text(encoding="utf-8", errors="ignore")
            if "\u2014" in text:
                issues.append((str(file.relative_to(root)), "em dash"))
            if CJK.search(text):
                issues.append((str(file.relative_to(root)), "CJK"))
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--quiz", type=Path, default=None)
    ap.add_argument("--pdf", type=Path, default=None)
    ap.add_argument("--expect-questions", type=int, default=None)
    args = ap.parse_args()

    if not args.root.exists():
        print(f"Root not found: {args.root}", file=sys.stderr)
        return 2

    failures = 0
    broken = check_links(args.root)
    print(f"links: {len(broken)} broken")
    for file, link in broken[:20]:
        print(f"  {file}: {link}")
    failures += len(broken)

    if args.quiz:
        errors, count, topics = check_quiz(args.quiz)
        print(f"quiz: {count} questions, {topics} topics, {len(errors)} errors")
        for error in errors[:20]:
            print(f"  {error}")
        failures += len(errors)

    if args.pdf:
        errors, count = check_pdf(args.pdf, args.expect_questions)
        print(f"pdf: {count} question IDs, {len(errors)} errors")
        for error in errors:
            print(f"  {error}")
        failures += len(errors)

    artifacts = check_artifacts(args.root)
    print(f"artifacts: {len(artifacts)} issues")
    for file, issue in artifacts[:20]:
        print(f"  {file}: {issue}")
    failures += len(artifacts)

    print("PASS" if failures == 0 else f"FAIL ({failures} issues)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
