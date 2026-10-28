#!/usr/bin/env python3
"""Check a generated study pack: links, quiz, PDF, delivery gates, and artifacts.

Usage:
  python check_site.py --root output --quiz output/assets/quiz-data.js
  python check_site.py --root output --brief output/sumber/project-brief.json \
    --quiz output/assets/quiz-data.js --pdf output/bank-soal/question-bank.pdf --strict
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from build_abbreviations import read_rows as read_abbr_rows, render as render_abbr
from check_coverage import validate_coverage
from quiz_schema import load_questions_file, validate_questions

SKIP_PREFIXES = ("http://", "https://", "#", "mailto:", "tel:", "javascript:", "data:")
CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
ABBR_TOKEN = re.compile(r"\b[A-Z][A-Z0-9&/]{1,7}\b")
CORE_BLOCKS = ("orientation", "essentials", "process", "traps", "self-check")
ABBR_STOP = {
    "DAN", "ATAU", "YANG", "UNTUK", "DENGAN", "PADA", "DARI", "KE", "DI", "BANK", "BUKAN",
    "HARUS", "WAJIB", "TIDAK", "ADALAH", "SEBAGAI", "DALAM", "OLEH", "AKAN", "DAPAT", "SETIAP",
    "SEMUA", "HAL", "BAB", "MODUL", "UNIT", "RISIKO", "MATERI", "SOAL", "KUNCI", "JAWABAN",
    "LATIHAN", "UJIAN", "NILAI", "TARGET", "PROSES", "LAPORAN", "BANK", "BUKU", "PETA",
    "MAP", "HOME", "TOPIC", "REFERENCE", "INTERVIEW", "QUIZ", "STUDY", "PACK", "BUILDER",
    "TEMPLATE", "PDF", "HTML", "CSS", "JS", "URL", "HTTP", "HTTPS", "CSV", "JSON", "XLSX",
    "DOCX", "PPTX", "SQL", "API", "UI", "UX", "ID", "IT", "AI", "OK", "IP", "CPU", "RAM",
    "SELF", "CHECK", "NEW", "NOTE", "FILES", "FLOW", "CONCEPTS", "PARAMETERS", "MEASUREMENT",
    "MONITORING", "REPORTING", "COVERAGE", "GLOSSARY", "ABBREVIATIONS", "CATEGORIES", "MATRIX",
    "ROUTE", "RELATIONSHIPS", "FOUNDATION", "RELIABILITY", "PRACTICE", "SOURCE", "DATA",
}


def html_files(root: Path):
    return sorted(root.rglob("*.html"))


def report(name, errors, warnings):
    print(f"{name}: {len(errors)} errors, {len(warnings)} warnings")
    for error in errors[:20]:
        print(f"  error: {error}")
    for warning in warnings[:20]:
        print(f"  warning: {warning}")
    return len(errors), len(warnings)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_js_object(path: Path, variable: str):
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(rf"{re.escape(variable)}\s*=\s*(\{{.*\}})\s*;", text, re.S)
    if not match:
        raise ValueError(f"{variable} object not found in {path}")
    return json.loads(match.group(1))


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
    try:
        data = load_questions_file(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"quiz data is invalid: {exc}"], 0, {}, [], []
    errors, warnings, stats = validate_questions(data)
    return errors, len(data), stats, warnings, data


def check_pdf(path: Path, expected: int | None):
    try:
        import pymupdf
    except ImportError:
        return ["pymupdf not installed; cannot check PDF"], 0
    doc = pymupdf.open(str(path))
    text = "".join(page.get_text() for page in doc)
    doc.close()
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


def check_brief(path: Path, root: Path, quiz_stats):
    errors = []
    warnings = []
    try:
        brief = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"brief is unreadable: {exc}"], warnings
    confirmed = brief.get("confirmed_at")
    if not confirmed:
        errors.append("brief is not confirmed; run scripts/confirm_brief.py after the user says yes")
    else:
        try:
            datetime.fromisoformat(str(confirmed).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"confirmed_at is not ISO 8601: {confirmed}")
    if not str(brief.get("confirmed_by") or "").strip():
        errors.append("confirmed_by is empty")
    for field in ("goal", "sources", "output", "language"):
        if not str(brief.get(field) or "").strip():
            errors.append(f"brief.{field} is empty")
    exam = brief.get("exam") if isinstance(brief.get("exam"), dict) else {}
    if not isinstance(exam.get("questions"), int) or exam.get("questions") < 1:
        errors.append("brief.exam.questions must be a positive integer")
    outputs = brief.get("outputs") if isinstance(brief.get("outputs"), dict) else {}
    if not outputs:
        errors.append("brief.outputs is missing")
    theme = brief.get("theme") if isinstance(brief.get("theme"), dict) else {}
    expected_mode = theme.get("mode")
    index_path = root / "index.html"
    if index_path.exists() and expected_mode in {"light", "dark"}:
        match = re.search(r'data-mode="([^"]+)"', index_path.read_text(encoding="utf-8", errors="ignore"))
        if match and match.group(1) != expected_mode:
            errors.append(f"index data-mode is {match.group(1)}, brief asks {expected_mode}")

    def require(name, relative, requested=True):
        path_obj = root / relative
        if requested and not path_obj.exists():
            errors.append(f"requested output missing: {relative}")
        elif not requested and path_obj.exists():
            warnings.append(f"{name} output exists but is disabled in the brief")

    require("website", "index.html", bool(outputs.get("website", True)))
    require("quiz page", "bank-soal.html", bool(outputs.get("quiz", True)))
    require("quiz data", "assets/quiz-data.js", bool(outputs.get("quiz", True)))
    require("print PDF", "bank-soal/question-bank.pdf", bool(outputs.get("print_pdf", True)))
    require("interview guide", "interview.html", bool(outputs.get("interview_guide", True)))
    video = brief.get("video") if isinstance(brief.get("video"), dict) else {}
    video_enabled = bool(outputs.get("video", False) or video.get("enabled", False))
    video_files = list((root / "video").glob("*.mp4")) if (root / "video").exists() else []
    if video_enabled and not video_files:
        errors.append("video is enabled but no video/*.mp4 file exists")
    if video_enabled and video.get("subtitles", True):
        if not list((root / "video").glob("*.srt")):
            errors.append("video is enabled but no SRT file exists")
    require("transcripts", "sumber/transcripts", bool(outputs.get("transcripts", False)))
    if outputs.get("transcripts"):
        transcript_dir = root / "sumber" / "transcripts"
        if transcript_dir.exists() and not list(transcript_dir.glob("*.srt")) and not list(transcript_dir.glob("*.txt")):
            errors.append("transcripts are enabled but sumber/transcripts has no .srt or .txt file")
    require("coverage map", "sumber/coverage-map.md", True)
    require("coverage audit", "sumber/coverage.json", True)
    require("source inventory", "sumber/source-inventory.json", True)
    coverage = root / "sumber" / "coverage-map.md"
    if coverage.exists() and "|" not in coverage.read_text(encoding="utf-8", errors="ignore"):
        errors.append("coverage-map.md has no table")
    if isinstance(exam.get("question_types"), list) and quiz_stats:
        for question_type in exam["question_types"]:
            if quiz_stats.get(question_type, 0) == 0:
                warnings.append(f"brief asks for {question_type} but the bank has none")
    return errors, warnings


def check_inventory(path: Path):
    errors = []
    warnings = []
    try:
        data = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"inventory is unreadable: {exc}"], warnings
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        return ["inventory has no sources"], warnings
    ssot = data.get("ssot")
    if not isinstance(ssot, list) or not ssot:
        errors.append("inventory has no SSOT")
        ssot = []
    by_path = {}
    for item in sources:
        if not isinstance(item, dict):
            errors.append("inventory source is not an object")
            continue
        source_path = str(item.get("path") or "").strip()
        if not source_path:
            errors.append("inventory source has no path")
        by_path[source_path] = item
        if item.get("role") not in {"primary", "assessment", "secondary"}:
            errors.append(f"{source_path}: invalid role {item.get('role')!r}")
        if not isinstance(item.get("supported"), bool):
            errors.append(f"{source_path}: supported must be true or false")
        if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256") or "")):
            errors.append(f"{source_path}: sha256 is missing or invalid")
        if item.get("role") == "primary" and not item.get("supported"):
            errors.append(f"{source_path}: primary source is unsupported")
        if source_path.startswith("/"):
            warnings.append(f"{source_path}: absolute path in a portable inventory")
    for source_path in ssot:
        item = by_path.get(source_path)
        if not item:
            errors.append(f"SSOT is not in sources: {source_path}")
        elif item.get("role") != "primary":
            errors.append(f"SSOT is not primary: {source_path}")
    if data.get("errors"):
        warnings.append(f"inventory recorded {data['errors']} build errors")
    return errors, warnings


def check_map(root: Path, questions, min_topics):
    errors = []
    warnings = []
    path = root / "assets" / "map-data.js"
    if not path.exists():
        return ["assets/map-data.js is missing"], warnings, None
    try:
        data = parse_js_object(path, "window.STUDY_MAP")
    except (ValueError, json.JSONDecodeError) as exc:
        return [f"map data is invalid: {exc}"], warnings, None
    topics = data.get("topics")
    if not isinstance(topics, list) or len(topics) < min_topics:
        errors.append(f"map must have at least {min_topics} categories")
        topics = topics if isinstance(topics, list) else []
    layers = data.get("layers")
    if not isinstance(layers, list) or len(layers) < 3:
        errors.append("map needs at least three layers")
        layers = []
    for layer in layers:
        if not isinstance(layer, dict) or not str(layer.get("title") or "").strip() or not str(layer.get("description") or "").strip():
            errors.append("every map layer needs a title and description")
    process = data.get("process")
    if not isinstance(process, list) or len(process) < 3:
        errors.append("map.process needs at least three steps")
        process = []
    weights = 0
    slugs = set()
    pages = set()
    for topic in topics:
        if not isinstance(topic, dict):
            errors.append("map topic is not an object")
            continue
        slug = str(topic.get("slug") or "").strip()
        title = str(topic.get("title") or "").strip()
        page = str(topic.get("page") or "").strip()
        source = str(topic.get("source") or "").strip()
        weight = topic.get("weight")
        kind = topic.get("kind") or "topic"
        if not slug or slug in slugs:
            errors.append(f"duplicate or empty map slug: {slug!r}")
        slugs.add(slug)
        if not title:
            errors.append(f"{slug}: empty title")
        if not page or page in pages:
            errors.append(f"{slug}: duplicate or empty page")
        pages.add(page)
        if page and not (root / page).exists():
            errors.append(f"{slug}: page does not exist: {page}")
        if not source:
            errors.append(f"{slug}: empty source range")
        if not isinstance(weight, (int, float)) or weight <= 0:
            errors.append(f"{slug}: weight must be a positive number")
        else:
            weights += weight
        if kind not in {"foundation", "topic"}:
            errors.append(f"{slug}: kind must be foundation or topic")
        matrix = topic.get("matrix")
        if not isinstance(matrix, dict):
            errors.append(f"{slug}: matrix is missing")
        else:
            for step in process:
                if not str(matrix.get(step) or "").strip():
                    errors.append(f"{slug}: matrix has no value for {step}")
        magnitude = topic.get("magnitude")
        if not isinstance(magnitude, dict):
            errors.append(f"{slug}: magnitude is missing")
        else:
            for field in ("slides", "concepts"):
                if not isinstance(magnitude.get(field), int) or magnitude.get(field) < 1:
                    errors.append(f"{slug}: magnitude.{field} must be a positive integer")
            if not isinstance(magnitude.get("formulas"), int) or magnitude.get("formulas") < 0:
                errors.append(f"{slug}: magnitude.formulas must be zero or a positive integer")
        big_ideas = topic.get("big_ideas")
        if not isinstance(big_ideas, list) or len(big_ideas) < 2:
            errors.append(f"{slug}: needs at least two big ideas")
            big_ideas = []
        idea_weights = 0
        concept_total = 0
        for idea_index, idea in enumerate(big_ideas, 1):
            if not isinstance(idea, dict):
                errors.append(f"{slug}: big idea {idea_index} is not an object")
                continue
            if not str(idea.get("title") or "").strip() or not str(idea.get("summary") or "").strip():
                errors.append(f"{slug}: big idea {idea_index} needs a title and summary")
            idea_weight = idea.get("weight")
            if not isinstance(idea_weight, (int, float)) or idea_weight <= 0:
                errors.append(f"{slug}: big idea {idea_index} needs a positive weight")
            else:
                idea_weights += idea_weight
            concepts = idea.get("concepts")
            if not isinstance(concepts, list) or len(concepts) < 2:
                errors.append(f"{slug}: big idea {idea_index} needs at least two concepts")
                concepts = []
            for concept in concepts:
                concept_total += 1
                if not isinstance(concept, dict):
                    errors.append(f"{slug}: concept is not an object")
                    continue
                for field in ("title", "gist", "source"):
                    if not str(concept.get(field) or "").strip():
                        errors.append(f"{slug}: concept in big idea {idea_index} has empty {field}")
        if big_ideas and abs(idea_weights - 100) > 0.5:
            errors.append(f"{slug}: big idea weights sum to {idea_weights}, expected 100")
        if isinstance(magnitude, dict) and magnitude.get("concepts") != concept_total:
            errors.append(f"{slug}: magnitude.concepts {magnitude.get('concepts')} does not match {concept_total} concepts")
        connections = topic.get("connections")
        if not isinstance(connections, list) or not connections:
            errors.append(f"{slug}: connections are missing")
        else:
            for connection in connections:
                if not isinstance(connection, dict):
                    errors.append(f"{slug}: connection is not an object")
                    continue
                if connection.get("to") not in {item.get("slug") for item in topics if isinstance(item, dict)}:
                    errors.append(f"{slug}: unknown connection target {connection.get('to')!r}")
                for field in ("relation", "mechanism"):
                    if not str(connection.get(field) or "").strip():
                        errors.append(f"{slug}: connection has empty {field}")
        for prerequisite in topic.get("prerequisites") or []:
            if prerequisite not in {item.get("slug") for item in topics if isinstance(item, dict)}:
                errors.append(f"{slug}: unknown prerequisite {prerequisite}")
        if questions is not None:
            quiz_topic = topic.get("quiz_topic")
            count = sum(1 for question in questions if question.get("topic") == quiz_topic) if quiz_topic else 0
            if quiz_topic and count == 0:
                warnings.append(f"{slug}: quiz topic has no questions: {quiz_topic}")
    if topics and abs(weights - 100) > 0.5:
        errors.append(f"map weights sum to {weights}, expected 100")
    for file_name in ("index.html", "map.html"):
        page_path = root / file_name
        if not page_path.exists():
            errors.append(f"missing {file_name}")
            continue
        markup = page_path.read_text(encoding="utf-8", errors="ignore")
        if "data-topic-map" not in markup:
            errors.append(f"{file_name} has no data-topic-map")
        if "map-data.js" not in markup:
            errors.append(f"{file_name} does not load map-data.js")
        if "map.js" not in markup:
            errors.append(f"{file_name} does not load map.js")
    map_page = root / "map.html"
    if map_page.exists():
        markup = map_page.read_text(encoding="utf-8", errors="ignore")
        for view in ("layers", "overview", "concepts", "matrix", "route", "relationships"):
            if f'data-study-map="{view}"' not in markup:
                errors.append(f"map.html has no {view} view")
    for topic in topics:
        if not isinstance(topic, dict) or not topic.get("page"):
            continue
        page_path = root / topic["page"]
        if page_path.exists():
            markup = page_path.read_text(encoding="utf-8", errors="ignore")
            if 'href="map.html"' not in markup and "href='map.html'" not in markup:
                warnings.append(f"{topic['page']}: no link back to map.html")
    return errors, warnings, data


def page_text(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def check_structure(root: Path, map_data):
    errors = []
    warnings = []
    if not map_data:
        return ["map data is required for structure checks"], warnings
    checked = 0
    for topic in map_data.get("topics") or []:
        if not isinstance(topic, dict):
            continue
        page = topic.get("page")
        if not page:
            continue
        path = root / page
        if not path.exists():
            errors.append(f"{page}: missing")
            continue
        markup = path.read_text(encoding="utf-8", errors="ignore")
        for block in CORE_BLOCKS:
            if f'data-study-block="{block}"' not in markup:
                errors.append(f"{page}: missing data-study-block={block}")
        if 'data-study-block="self-check"' in markup and "<details" not in markup:
            errors.append(f"{page}: self-check has no details element")
        if not re.search(r'data-source-range="([^"]+)"', markup):
            errors.append(f"{page}: missing non-empty data-source-range")
        if len(re.findall(r"<h1\b", markup, re.I)) != 1:
            errors.append(f"{page}: expected exactly one h1")
        if len(re.findall(r"<h2\b", markup, re.I)) < 2:
            errors.append(f"{page}: expected at least two h2 sections")
        checked += 1
    if not checked:
        errors.append("no map topic pages were checked")
    return errors, warnings


def check_abbreviations(root: Path):
    errors = []
    warnings = []
    path = root / "assets" / "abbreviations.js"
    if not path.exists():
        return ["assets/abbreviations.js is missing"], warnings
    try:
        data = parse_js_object(path, "window.ABBREVIATIONS")
    except (ValueError, json.JSONDecodeError) as exc:
        return [f"abbreviations data is invalid: {exc}"], warnings
    if not isinstance(data, dict) or not data:
        return ["abbreviations data is empty"], warnings
    for key, value in data.items():
        expansion = value.get("expansion") if isinstance(value, dict) else value
        if not str(expansion or "").strip():
            errors.append(f"{key}: empty expansion")
    site = root / "assets" / "site.js"
    if site.exists() and "window.ABBREVIATIONS" not in site.read_text(encoding="utf-8", errors="ignore"):
        errors.append("site.js does not read window.ABBREVIATIONS")
    reference = root / "reference.html"
    if not reference.exists():
        errors.append("reference.html is missing")
    else:
        markup = reference.read_text(encoding="utf-8", errors="ignore")
        if len(re.findall(r"data-abbr-row", markup)) < 3:
            errors.append("reference.html has fewer than 3 abbreviation rows")
        if "data-abbr-search" not in markup:
            errors.append("reference.html has no abbreviation search box")
        try:
            rows, row_errors = read_abbr_rows(reference)
            if row_errors:
                errors.extend(row_errors)
            elif render_abbr(rows) != path.read_text(encoding="utf-8"):
                errors.append("assets/abbreviations.js is out of date; run scripts/build_abbreviations.py")
        except OSError as exc:
            errors.append(f"cannot compare abbreviations: {exc}")
    content = []
    for page in ["index.html", "foundation.html", "interview.html", "reference.html"] + [p.name for p in root.glob("topic*.html")] + [p.name for p in root.glob("topik*.html")]:
        page_path = root / page
        if page_path.exists():
            content.append(page_text(page_path))
    local_ignore = set()
    ignore_path = root / "assets" / "abbreviations.ignore"
    if ignore_path.exists():
        local_ignore = {token.strip() for token in ignore_path.read_text(encoding="utf-8").split() if token.strip()}
    counts = {}
    for token in ABBR_TOKEN.findall(" ".join(content)):
        if token in ABBR_STOP or token in local_ignore or token in data:
            continue
        counts[token] = counts.get(token, 0) + 1
    for token, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:12]:
        if count >= 3:
            warnings.append(f"frequent acronym not in abbreviations.js: {token} ({count})")
    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--quiz", type=Path, default=None)
    ap.add_argument("--pdf", type=Path, default=None)
    ap.add_argument("--expect-questions", type=int, default=None)
    ap.add_argument("--brief", type=Path, default=None, help="Enable delivery gates for a study pack")
    ap.add_argument("--inventory", type=Path, default=None, help="Default: <root>/sumber/source-inventory.json")
    ap.add_argument("--min-topics", type=int, default=2, help="Minimum map categories for this check")
    ap.add_argument("--coverage", type=Path, default=None, help="Default: <root>/sumber/coverage.json")
    ap.add_argument("--normalized", type=Path, default=None, help="Optional normalized JSONL for unit-level coverage comparison")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = ap.parse_args()

    if not args.root.exists():
        print(f"Root not found: {args.root}", file=sys.stderr)
        return 2

    failures = 0
    warning_total = 0

    broken = check_links(args.root)
    print(f"links: {len(broken)} broken")
    for file, link in broken[:20]:
        print(f"  {file}: {link}")
    failures += len(broken)

    questions = None
    quiz_stats = {}
    if args.quiz:
        errors, count, stats, warnings, questions = check_quiz(args.quiz)
        types = ", ".join(f"{key}={value}" for key, value in sorted(stats.get("by_type", {}).items()))
        print(f"quiz: {count} questions, {len(stats.get('topics', []))} topics, {len(errors)} errors, {len(warnings)} warnings")
        if types:
            print(f"  types: {types}")
        for error in errors[:20]:
            print(f"  error: {error}")
        for warning in warnings[:20]:
            print(f"  warning: {warning}")
        failures += len(errors)
        warning_total += len(warnings)
        quiz_stats = stats.get("by_type", {})

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

    if args.brief:
        sections = []
        errors, warnings = check_brief(args.brief, args.root, quiz_stats)
        sections.append(("brief", errors, warnings))
        inventory_path = args.inventory or (args.root / "sumber" / "source-inventory.json")
        errors, warnings = check_inventory(inventory_path)
        sections.append(("inventory", errors, warnings))
        errors, warnings, map_data = check_map(args.root, questions, args.min_topics)
        sections.append(("map", errors, warnings))
        errors, warnings = check_structure(args.root, map_data)
        sections.append(("structure", errors, warnings))
        coverage_path = args.coverage or (args.root / "sumber" / "coverage.json")
        coverage_errors, coverage_warnings, coverage_stats = validate_coverage(
            coverage_path, args.root, questions, args.normalized
        )
        sections.append(("coverage", coverage_errors, coverage_warnings))
        print(
            f"coverage: {coverage_stats.get('total', 0)} units, "
            f"{coverage_stats.get('covered', 0)} covered, "
            f"{coverage_stats.get('non-content', 0)} non-content, "
            f"{coverage_stats.get('unresolved', 0)} unresolved"
        )
        errors, warnings = check_abbreviations(args.root)
        sections.append(("abbreviations", errors, warnings))
        for name, errors, warnings in sections:
            failures += report(name, errors, warnings)[0]
            warning_total += len(warnings)

    if args.strict:
        failures += warning_total
    print("PASS" if failures == 0 else f"FAIL ({failures} issues)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
