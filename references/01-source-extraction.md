# Source Extraction

## Goal

Turn every source into searchable text with page, slide, or timestamp references before writing summaries.

## Inventory

Record:

| Source | Type | Count | Pages or duration | Text layer | Notes |
|---|---|---|---|---|---|
| deck.pdf | PDF | 1 | 120 | yes | primary |
| deck.pptx | PPTX | 1 | 120 | yes | speaker notes? |
| session-1.m4a | audio | 1 | 1h42m | n/a | duplicate compressed copy exists |
| answer-1.pdf | PDF | 1 | 6 | yes | highlights contain keys |
| forms-1.pdf | PDF | 1 | 8 | no | screenshots, needs OCR |

Store raw extraction in `working/`, not in the final deliverable.

## PDF

Use PyMuPDF. It preserves page numbers and coordinates.

```bash
python scripts/extract_pdf.py deck.pdf --out working/deck.json
```

The script returns `pages[]` with `page` and `text`, plus the table of contents. Check for pages with fewer than 30 characters. Those are probably images and need OCR.

For scanned PDFs:

```bash
pdftoppm -r 200 -png scanned.pdf working/scan
for f in working/scan-*.png; do scripts/ocr.sh "$f" > "${f%.png}.txt"; done
```

## PPTX

```python
from pptx import Presentation
prs = Presentation("deck.pptx")
for i, slide in enumerate(prs.slides, 1):
    texts = []
    for shape in slide.shapes:
        if hasattr(shape, "text") and shape.text.strip():
            texts.append(shape.text.strip())
    notes = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
    print(i, "\n".join(texts), "\nNOTES:", notes)
```

Speaker notes often contain the instructor's real emphasis. Extract them even if the deck text is complete.

## OCR

macOS Vision is fast and accurate for screenshots and image-only PDFs.

```bash
scripts/ocr.sh screenshot.png > working/screenshot.txt
```

The output is tab-separated: `x`, `y`, `width`, `height`, `text`, sorted top to bottom. Preserve coordinates when reconstructing questions or tables.

On non-macOS systems use Tesseract:

```bash
tesseract screenshot.png stdout -l ind+eng
```

OCR is not perfect. Review numbers, abbreviations, and similar characters (`l` vs `1`, `O` vs `0`).

## Audio

On Apple Silicon, `mlx-whisper` with a large turbo model is a good speed/accuracy tradeoff.

```bash
mlx_whisper session.m4a \
  --model mlx-community/whisper-large-v3-turbo \
  --language id \
  --initial-prompt "Domain terms, acronyms, and names." \
  --output-dir working/transcripts \
  --output-name session-1 \
  --output-format all \
  --verbose False
```

Rules:

- Skip compressed duplicate copies. Check duration and filename.
- Transcribe sequentially if the GPU is shared. Parallel Whisper processes often halve total throughput.
- Keep SRT, TXT, and a readable paragraph version.
- Mark transcripts as machine-generated.

Convert SRT to readable paragraphs:

```bash
python scripts/srt_to_paragraphs.py working/transcripts/session-1.srt
```

Search advice with multiple markers: `interview`, `exam`, `question`, `remember`, `often`, `definition`, `factor`, `trap`, `focus`. Read the surrounding segment, not just the keyword line.

## Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| Empty PDF pages | scanned images | OCR |
| Garbled PDF text | bad encoding or columns | render and OCR |
| Key missing | no highlight or low contrast | cross-check duplicate source |
| OCR numbers wrong | small font or font substitution | manual review |
| Transcript names wrong | uncommon proper nouns | add initial prompt, verify against slides |
| Audio advice contradicts slides | speaker simplification | slides win, note the difference |
