#!/bin/bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$DIR/.ocr-bin"
if [ ! -x "$BIN" ]; then
  if ! command -v swiftc >/dev/null 2>&1; then
    echo "swiftc not found. Use Tesseract instead: tesseract image.png stdout -l ind+eng" >&2
    exit 2
  fi
  swiftc -O "$DIR/ocr_vision.swift" -o "$BIN"
fi
if [ $# -lt 1 ]; then
  echo "usage: ocr.sh <image>" >&2
  exit 2
fi
"$BIN" "$1"
