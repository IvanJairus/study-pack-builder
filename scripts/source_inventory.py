#!/usr/bin/env python3
"""Build a source inventory with SSOT, roles, hashes, and support status.

The inventory records what exists and which files are authoritative. It does
not extract content. Use normalize_source.py after the inventory is clear.

Usage:
  python source_inventory.py sources/ --out sumber/source-inventory.json
  python source_inventory.py sources/ --out sumber/source-inventory.json --brief sumber/project-brief.json
  python source_inventory.py sources/ --out ... --normalized working/normalized.summary.json
"""
import argparse
import fnmatch
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import normalize_source

SUPPORTED = (
    normalize_source.TEXT_EXT
    | normalize_source.HTML_EXT
    | normalize_source.DOCX_EXT
    | normalize_source.LEGACY_DOC_EXT
    | normalize_source.EPUB_EXT
    | normalize_source.CSV_EXT
    | normalize_source.XLSX_EXT
    | normalize_source.PDF_EXT
    | normalize_source.PPTX_EXT
)
AUDIO_EXT = {".m4a", ".mp3", ".wav", ".aac", ".mp4", ".mov", ".mkv"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp", ".svg", ".gif"}
SKIP_DIRS = normalize_source.SKIP_DIRS | {"working", "study-pack", "output", "outputs"}
ASSESSMENT_PATTERNS = ["*soal*", "*question*", "*jawaban*", "*kunci*", "*answer*", "*quiz*", "*bank*"]
ADAPTERS = {
    **{ext: "normalize_source:text" for ext in normalize_source.TEXT_EXT},
    **{ext: "normalize_source:html" for ext in normalize_source.HTML_EXT},
    **{ext: "normalize_source:docx" for ext in normalize_source.DOCX_EXT},
    **{ext: "normalize_source:legacy" for ext in normalize_source.LEGACY_DOC_EXT},
    **{ext: "normalize_source:epub" for ext in normalize_source.EPUB_EXT},
    **{ext: "normalize_source:csv" for ext in normalize_source.CSV_EXT},
    **{ext: "normalize_source:xlsx" for ext in normalize_source.XLSX_EXT},
    **{ext: "normalize_source:pdf" for ext in normalize_source.PDF_EXT},
    **{ext: "normalize_source:pptx" for ext in normalize_source.PPTX_EXT},
}
VALID_ROLES = {"primary", "assessment", "secondary", "ignored"}
QUIET = False


def log(message):
    if not QUIET:
        print(f"[inventory] {message}", file=sys.stderr)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def match_path(path, pattern):
    display = path.as_posix()
    if fnmatch.fnmatch(display, pattern) or fnmatch.fnmatch(path.name, pattern):
        return True
    if "/" in pattern and not pattern.startswith("/"):
        return fnmatch.fnmatch(display, f"*/{pattern}")
    return False


def matches(path, patterns):
    return any(match_path(path, pattern) for pattern in patterns)


def scan(paths):
    files = []
    skipped = []
    seen = set()
    for raw in paths:
        root = Path(raw).expanduser()
        if not root.exists():
            skipped.append({"path": str(root), "reason": "not found"})
            continue
        candidates = [root] if root.is_file() else sorted(root.rglob("*"))
        for candidate in candidates:
            if not candidate.is_file():
                continue
            if candidate.name.startswith(".") or candidate.name.startswith("~$"):
                continue
            if any(part in SKIP_DIRS for part in candidate.parts):
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(candidate)
    return files, skipped


def default_role(path):
    suffix = path.suffix.lower()
    if suffix in AUDIO_EXT or suffix in IMAGE_EXT:
        return "secondary"
    if any(fnmatch.fnmatch(path.name.lower(), pattern) for pattern in ASSESSMENT_PATTERNS):
        return "assessment"
    return "primary"


def role_overrides(brief):
    result = []
    for item in brief.get("source_roles", []) if isinstance(brief, dict) else []:
        if isinstance(item, dict) and item.get("pattern") and item.get("role") in VALID_ROLES:
            result.append((item["pattern"], item["role"]))
    return result


def apply_role(path, overrides):
    role = default_role(path)
    for pattern, override in overrides:
        if match_path(path, pattern):
            role = override
    return role


def units_map(summary_path):
    if not summary_path:
        return {}
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    result = {}
    for item in data.get("sources", []):
        source = item.get("source", "")
        if source:
            result[Path(source).name] = item.get("units", 0)
    return result


def main():
    global QUIET
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", help="Source files or folders")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--brief", type=Path, default=None)
    parser.add_argument("--normalized", type=Path, default=None, help="normalized.summary.json for unit counts")
    parser.add_argument("--base", type=Path, default=Path.cwd(), help="Base for relative paths")
    parser.add_argument("--ignore", action="append", default=[], help="Additional ignore glob")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    QUIET = args.quiet

    brief = {}
    if args.brief:
        try:
            brief = json.loads(args.brief.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Cannot read brief: {exc}", file=sys.stderr)
            return 2

    ignore_patterns = list(brief.get("ignore", [])) if isinstance(brief.get("ignore"), list) else []
    ignore_patterns.extend(args.ignore)
    overrides = role_overrides(brief)
    units = units_map(args.normalized)

    files, missing = scan(args.paths)
    log(f"scan: {len(files)} files, {len(ignore_patterns)} ignore patterns")

    sources = []
    ignored = []
    errors = 0
    for path in files:
        try:
            display = os.path.relpath(path.resolve(), args.base.resolve())
        except ValueError:
            display = str(path.resolve())
        if display.startswith(".."):
            display = path.resolve().as_posix()
        suffix = path.suffix.lower()
        supported = suffix in SUPPORTED
        adapter = ADAPTERS.get(suffix, "")
        role = apply_role(path, overrides)
        if matches(path, ignore_patterns):
            role = "ignored"
        info = {
            "path": display,
            "format": suffix.lstrip(".") or "(none)",
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
            "supported": supported,
            "adapter": adapter,
            "role": role,
            "units": units.get(path.name, 0),
        }
        if not supported:
            info["reason"] = normalize_source.unsupported_hint(suffix)
        if role == "ignored":
            ignored.append(info)
            continue
        sources.append(info)
        if not supported and role in {"primary", "assessment"}:
            errors += 1
            log(f"unsupported {role}: {display} ({info.get('reason', '')})")

    primary = [item for item in sources if item["role"] == "primary"]
    ssot_patterns = brief.get("ssot", []) if isinstance(brief, dict) else []
    if ssot_patterns:
        ssot = []
        for pattern in ssot_patterns:
            matched = [item["path"] for item in sources if fnmatch.fnmatch(item["path"], pattern) or fnmatch.fnmatch(Path(item["path"]).name, pattern)]
            if not matched:
                errors += 1
                log(f"SSOT pattern matched nothing: {pattern}")
            for item in matched:
                if item not in ssot:
                    ssot.append(item)
    else:
        ssot = [item["path"] for item in primary]

    if not primary and not ssot:
        errors += 1
        log("no primary source found")
    for path in ssot:
        item = next((source for source in sources if source["path"] == path), None)
        if item and item["role"] != "primary":
            errors += 1
            log(f"SSOT is not primary: {path} ({item['role']})")

    counts = {
        "files": len(sources),
        "primary": sum(1 for item in sources if item["role"] == "primary"),
        "assessment": sum(1 for item in sources if item["role"] == "assessment"),
        "secondary": sum(1 for item in sources if item["role"] == "secondary"),
        "ignored": len(ignored),
        "unsupported": sum(1 for item in sources if not item["supported"]),
    }
    inventory = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": str(args.base.resolve()),
        "ssot": ssot,
        "counts": counts,
        "sources": sources,
        "ignored": ignored,
        "missing": missing,
        "errors": errors,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"files={counts['files']} primary={counts['primary']} assessment={counts['assessment']} secondary={counts['secondary']} ignored={counts['ignored']} unsupported={counts['unsupported']}")
    print(f"ssot={len(ssot)} errors={errors}")
    print(f"wrote {args.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
