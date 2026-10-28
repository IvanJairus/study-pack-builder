# Format Adapters

## Goal

Turn every text-bearing source into one JSONL stream with a stable reference before the agent writes summaries. The normalized file is working data. Do not ship it as the final deliverable.

```bash
python scripts/normalize_source.py sources/ --out working/normalized.jsonl
```

The script writes `working/normalized.jsonl` and `working/normalized.summary.json`. Debug lines go to stderr and show each file, record count, character count, converter, and error.

## Record schema

One JSON object per line:

```json
{
  "source": "sources/handout.docx",
  "format": "docx",
  "unit": "paragraph",
  "ref": "paragraph:12",
  "section": "Liquidity > Measurement",
  "text": "Liquidity coverage ratio equals high quality liquid assets divided by net cash outflow.",
  "meta": {"style": "Normal"}
}
```

Fields:

- `source`: path used during normalization.
- `format`: `txt`, `md`, `html`, `docx`, `doc`, `epub`, `csv`, `xlsx`, `pdf`, or `pptx`.
- `unit`: `page`, `slide`, `paragraph`, `heading`, `line`, `block`, `row`, `header`, `list_item`, `code`, or `note`.
- `ref`: anchor inside the source. Use it in the coverage map.
- `section`: heading path, chapter, or sheet name.
- `text`: cleaned text.
- `meta`: optional table cells, columns, language, or part numbers.

Long blocks are split at `--max-chars` (default 4000). Split records append `!part:N` to the ref.

## Anchors

| Source | Ref examples |
|---|---|
| PDF | `page:3` |
| PPTX | `slide:4`, `slide:4!notes` |
| DOCX | `paragraph:12`, `table:2!row:3` |
| TXT | `line:10-14` |
| Markdown | `line:8`, `line:20-22` |
| HTML | `line:12`, `line:20-24` |
| EPUB | `chapter:2!line:8-10` |
| CSV | `row:7` |
| XLSX | `sheet:Liquidity!row:7` |

Every anchor must resolve to one source location. If a parser cannot produce an anchor, mark the source as unresolved instead of inventing one.

## Supported formats

| Format | Method | Notes |
|---|---|---|
| TXT | Native read | UTF-8 first, then cp1252 and latin-1 |
| Markdown | Native parser | Headings, lists, tables, code fences, frontmatter skipped |
| HTML | Standard library parser | Skips navigation, scripts, styles, forms, and footers; keeps headings and table rows |
| DOCX | XML inside the ZIP | Paragraph order, heading styles, tables; no images or text boxes |
| DOC, RTF | `textutil` or LibreOffice | Converted to plain text; tables lose structure |
| EPUB | ZIP, OPF spine order | Reads chapters in spine order, not filename order |
| CSV, TSV | Standard library csv | First non-empty row becomes the header |
| XLSX, XLSM | XML inside the ZIP | Shared strings, inline strings, sheets, physical row numbers; macros are never executed |
| PDF | PyMuPDF when installed | One record per non-empty page; scanned pages need OCR first |
| PPTX | python-pptx when installed | Slide text plus speaker notes |

Images and audio are not normalized here. Use `scripts/ocr.sh` for images and the Whisper pipeline for audio, then normalize the OCR text or transcript.

## Commands

```bash
python scripts/normalize_source.py sources/ --out working/normalized.jsonl
python scripts/normalize_source.py sources/ --out working/normalized.jsonl --ext .docx,.csv
python scripts/normalize_source.py sources/ --out working/normalized.jsonl --exclude 'old/*'
python scripts/normalize_source.py sources/ --out working/normalized.jsonl --max-chars 2500
```

`--no-summary` skips the sidecar. `--quiet` hides debug lines. The exit code is 1 when any supported file fails to parse, even if other files succeed.

## Tables and spreadsheets

- The first non-empty row is the header.
- Empty headers become `Column A`, `Column B`, and so on.
- Duplicate headers get a numeric suffix, such as `Score (2)`.
- Each data row becomes `Header: value | Header: value`.
- Physical row numbers are preserved. Blank rows are skipped but do not renumber later rows.
- A separate `header` record captures the column names.
- XLSX dates remain serial numbers because cell styles are not applied. Verify dates manually before using them in content.
- CSV delimiter detection tries comma, semicolon, tab, and pipe, then falls back to comma or tab by extension.

## Legacy DOC

The adapter tries converters in this order:

1. `textutil` on macOS.
2. `soffice` or `libreoffice` in headless mode.
3. A clear error that asks for LibreOffice or a DOCX conversion.

Plain text conversion loses tables, highlighting, and comments. If the document contains tables or marked answers, convert it to DOCX first and normalize the DOCX so table structure is preserved.

## HTML and EPUB noise

The HTML parser drops navigation, sidebars, forms, scripts, styles, and footers. It keeps headings, paragraphs, lists, and table rows. An HTML export with the main content inside a skipped element will produce too little text. Check the summary record count and inspect the output when a file looks empty.

EPUB chapters are read in spine order from the OPF file. If the spine is missing, the adapter falls back to manifest HTML files, then to sorted XHTML files.

## XML safety

OOXML and EPUB XML are parsed with entity and DTD declarations rejected. Archive members above 50 MB are refused before decompression, so a crafted file cannot exhaust memory through one oversized part. Macros in XLSM and DOCM are never executed. Files stay local. The normalizer makes no network requests.

## Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| 0 records for a file | content inside skipped HTML element, or empty document | Inspect the source and the debug log |
| DOC conversion error | no `textutil` and no LibreOffice | Install LibreOffice or convert to DOCX |
| Table row text is empty | merged cells or nested tables | Read the source table manually |
| XLSX dates look like 45200 | date style not applied | Convert the date manually |
| Scanned PDF has empty pages | image-only pages | Run OCR, then normalize the OCR text |
| Many skipped files | images, audio, or legacy formats | Use the hint printed for each skipped file |

## Coverage map integration

Use the ref values directly in the coverage map:

| Source | Ref | Content | Output page | Status |
|---|---|---|---|---|
| handout.docx | paragraph:12 | Liquidity ratio definition | liquidity.html | covered |
| bank.xlsx | Liquidity!row:7 | LCR question | bank-soal.html | covered |
| notes.md | line:20-22 | Exam advice | interview.html | covered |
| deck.pdf | page:44 | Diagram only | none | non-content |

Every normalized record must map to an output page or be marked as non-content.
