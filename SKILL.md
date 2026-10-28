---
name: study-pack-builder
description: Build a complete study pack from mixed local sources such as PDF, PPTX, DOCX, HTML, EPUB, TXT, Markdown, CSV, XLSX, audio recordings, and question banks. Use when the user wants a structured study website, a deduplicated exam question bank with explanations, a printable PDF, a narrated overview video, interview notes, or a repeatable source-to-study-pack pipeline with verification.
---

# Study Pack Builder

## Overview

Turn a folder of heterogeneous study material into a coherent, verified study pack: topic architecture, readable website, deduplicated question bank, printable PDF, narrated video, and a coverage map. The source material is the authority. Audio is complementary. Every output must be traceable to a source and checked before delivery.

## Use when

- The user has slides, PDFs, recordings, and question files for an exam or certification.
- The user wants duplicate questions merged into one question bank with answers and explanations.
- The user wants a study website, printable question bank, narrated overview, or interview preparation.
- The user wants a repeatable pipeline rather than a one-off summary.

Do not use for a single-document summary, a generic essay, or publishing proprietary material.

## Non-negotiables

1. Keep the source deck/PDF as the primary foundation. Use audio only for advice, emphasis, and interview hints.
2. Never publish confidential, proprietary, personal, or licensed source files. Use synthetic examples in public repositories.
3. Never invent an answer. If a key cannot be read, fill it from a duplicate or mark it unresolved for review.
4. Preserve traceability: source file, page/slide range, timestamp, or question ID.
5. Verify before delivery. A green build is not proof that the study pack is correct or usable.

## Project brief

Read `references/08-project-brief.md` and copy `assets/project-brief.example.json` before extraction. Ask the eight choices in one batch, then write the brief to `sumber/project-brief.json`.

1. Source folder and output folder.
2. Exam shape: questions, minutes, interview.
3. Language.
4. Outputs: website, quiz, print PDF, video, interview guide, transcripts.
5. Video: yes or no, minutes, voice, subtitles.
6. Theme: light, dark, or system.
7. Audio transcription and files to ignore.
8. Distribution and confidentiality constraints.

Defaults: source language, light theme, video off unless requested, 5 minutes when enabled, print PDF and quiz on, interview guide on when the exam has an interview, local processing only.

## Workflow

### 1. Inventory and extract

Create a source inventory before writing content.

- List file types, counts, pages, durations, and whether text is selectable.
- When the folder contains TXT, Markdown, HTML, DOCX, DOC, RTF, EPUB, CSV, TSV, or XLSX, run `scripts/normalize_source.py` to produce one JSONL stream with stable refs.
- Extract PDF text per page with `scripts/extract_pdf.py`.
- Extract PPTX text and speaker notes with `python-pptx`.
- OCR image-only PDFs and screenshots with `scripts/ocr.sh` on macOS Vision, or Tesseract elsewhere.
- Transcribe audio with `mlx-whisper` on Apple Silicon, or `whisper.cpp`/`faster-whisper` elsewhere.
- Convert SRT to readable timestamped paragraphs with `scripts/srt_to_paragraphs.py`.
- Keep raw extraction in a working directory, never in the final deliverable.

```bash
python scripts/normalize_source.py sources/ --out working/normalized.jsonl
```

Read `references/01-source-extraction.md` for commands and `references/09-format-adapters.md` for the JSONL schema, anchors, converters, and format limits.

### 2. Derive the study architecture

Derive topics from the source, not from a fixed template.

- Group material into 5 to 8 major clusters plus a foundation/orientation page.
- Build one matrix: clusters x the source's recurring process (for example identify, measure, monitor, communicate).
- Add a relationship map for cross-topic effects.
- Map every slide/page range to exactly one output page.
- Identify cross-cutting themes such as regulation, climate, cyber, or reporting.

Read `references/03-content-architecture.md` for page structure and coverage mapping.

### 3. Build the question bank

1. Extract questions and options from PDFs. If answers are highlighted, detect the highlight rectangles and map them to option lines with `scripts/extract_questions.py`. Option letters may run from A to H.
2. Cross-check with other question sources such as forms, answer keys, CSV or XLSX exports, and screenshots.
3. Fill missing keys only from duplicates. Keep a list of unresolved items.
4. Normalize text, cluster duplicates with `scripts/dedup_questions.py`, and choose one canonical wording per cluster. Only cluster the same question type.
5. Preserve every raw question ID in the cluster members. Every raw question must appear exactly once.
6. Choose a type for every unique question: `single_choice`, `multiple_choice`, `true_false`, or `short_answer`. Choice questions need at least 2 options; 8 or fewer reads better.
7. Write an explanation for every unique question: why the key is right, why the main distractors are wrong, and the exam trap. Ground explanations in the source material.
8. Validate the final bank with `scripts/quiz_schema.py`. Answers must match the type, and every question needs a topic, explanation, and trap.

Read `references/02-question-bank.md` for the schema, type rules, heuristics, and validation.

### 4. Extract audio advice

- Transcribe all usable recordings. Skip duplicate compressed copies.
- Search for advice markers: exam, interview, question, remember, often, definition, factor, trap, focus.
- Convert each useful segment into a short note with session and timestamp.
- Group notes by theme, not by chronology. Remove repeated advice.
- Keep the transcript files as a source appendix, clearly marked as machine-generated.

### 5. Write the study content

For each topic page, use this order:

1. One-sentence orientation.
2. "30-second essentials" with three to five bullets.
3. The recurring process as a visual sequence.
4. Definitions and scope.
5. Factors or parameters in a table.
6. Measurement methods and formulas.
7. Monitoring and controls.
8. Reporting frequency and recipients.
9. Exam traps.
10. Self-check questions.
11. Source ranges.

Prefer tables, short lists, formulas, and labeled diagrams over long prose. Do not copy the source verbatim.

### 6. Build the outputs

Build only the outputs enabled in the brief. Skip video scripting, TTS, slides, and rendering when video is off.

- Website: static, offline, light or dark theme, system fonts, responsive, no CDN.
- Quiz: filter by topic, search, shuffle, reveal answer, explanation, trap, retry wrong, list mode, local progress. Support single choice, multiple choice, true or false, and short answer with variable option counts.
- Print PDF: a print stylesheet with all questions, keys, and explanations, rendered with headless Chrome.
- Video: requested duration, narrated TTS, screenshots of the site, title/bullets/takeaway, SRT.
- Reference pages: glossary, abbreviations with tooltips, coverage map.

Read `references/04-site-build.md` and `references/05-video.md` before implementing.

### 7. Verify and deliver

Run all checks:

- Every source page, slide, paragraph, line range, or row is mapped to an output page.
- Every raw question is mapped exactly once.
- Every answer matches its question type; choice questions have at least 2 options; explanation and trap are present.
- Zero broken relative links.
- Quiz interactions work for all four question types on desktop and mobile.
- No console errors.
- Light and dark themes render correctly at 390 px and 1440 px.
- PDF contains the expected number of questions.
- Video duration, audio levels, slide sync, and SRT match.
- No em dash or unintended CJK characters in artifacts.
- No proprietary files in the distributed folder or repository.

Read `references/06-verification.md` for commands and acceptance gates.

## Output layout

Use a predictable layout so the user can navigate without instructions.

```text
study-pack/
├── index.html
├── peta-topik.html
├── foundation.html
├── topic-01.html ... topic-06.html
├── bank-soal.html
├── interview.html
├── bank-soal/
│   ├── index.html
│   └── question-bank.pdf
├── assets/
│   ├── css/style.css
│   ├── js/site.js
│   ├── js/quiz.js
│   └── js/quiz-data.js
├── video/
│   ├── overview.mp4
│   ├── overview.srt
│   └── script.md
└── sumber/
    ├── coverage-map.md
    └── transcripts/
```

## Quality gates

| Gate | Pass condition |
|---|---|
| Source coverage | Every page, slide, paragraph, line range, or row has a destination or is explicitly marked as non-content |
| Source formats | Every supported source is normalized or explicitly skipped; summary errors are reviewed |
| Question coverage | Every raw question ID appears once in a cluster |
| Question schema | `quiz_schema.py` reports 0 errors; warnings are reviewed |
| Answer integrity | Answer matches the type; options are valid; no blank explanation or trap |
| Site integrity | 0 broken links; 0 console errors; all quiz types tested |
| Responsive | 390 px and 1440 px checked; no horizontal overflow except intentional tables |
| Print | PDF opens; expected question count; readable at A4 |
| Video | Duration matches target; audio audible; frames match sections; SRT valid |
| Distribution | No source PDFs, audio, screenshots, personal data, or logos in the public repo |
| Brief | Every requested output is built; skipped outputs are reported |
| Theme | Light and dark modes both keep readable contrast if dark is selected |

## Resources

- `scripts/extract_pdf.py`: text per page and TOC.
- `scripts/normalize_source.py`: mixed formats to JSONL with line, paragraph, and row refs.
- `scripts/extract_questions.py`: highlighted answers to structured JSON, option letters A to H.
- `scripts/dedup_questions.py`: fuzzy clustering, type-aware, answer conflict flags.
- `scripts/quiz_schema.py`: validate question types, options, answers, and explanations.
- `scripts/ocr_vision.swift` and `scripts/ocr.sh`: macOS Vision OCR.
- `scripts/srt_to_paragraphs.py`: timestamped readable transcripts.
- `scripts/tts_say.py`: macOS TTS for video narration.
- `scripts/make_slides.py`: white-theme 1920x1080 slides from a script JSON.
- `scripts/render_video.py`: segments, intro/outro, concat, AAC/H.264.
- `scripts/check_site.py`: links, quiz schema, PDF count, artifact scan.
- `references/01-07`: detailed procedures and guardrails.
- `references/08-project-brief.md`: question list, defaults, and brief schema.
- `references/09-format-adapters.md`: supported formats, anchors, converters, and limits.
- `assets/project-brief.example.json`: copyable brief.
- `assets/site-template/`: offline study-site starter with light and dark modes.
- `assets/video-template/script.example.json`: video script schema.
- `examples/synthetic/`: safe test data, including `questions-flexible.json`.

## Install

Fast path with npx. It detects installed agents and writes the skill into each one:

```bash
npx github:IvanJairus/study-pack-builder
```

Inspect detection first:

```bash
npx github:IvanJairus/study-pack-builder --list
```

After the package is published to npm, the shorter form is:

```bash
npx study-pack-builder
```

Supported agents and user-level paths:

| Agent | Install path |
|---|---|
| Qoder | `~/.qoder/skills/study-pack-builder` |
| Claude Code | `~/.claude/skills/study-pack-builder` |
| Cursor | `~/.cursor/skills/study-pack-builder` |
| Antigravity | `~/.gemini/antigravity/skills/study-pack-builder` |
| Codex | `~/.codex/skills/study-pack-builder` |

Project-level install:

```bash
npx github:IvanJairus/study-pack-builder --project
```

Installer options: `--list`, `--all`, `--agent <ids>`, `--project`, `--target <path>`, `--force`, `--dry-run`.
Existing installs are skipped unless `--force` is used; forced updates back up to `~/.study-pack-builder/backups/`.

Manual clone as a fallback:

```bash
git clone https://github.com/IvanJairus/study-pack-builder.git \
  ~/.qoder/skills/study-pack-builder
```

Reload skills, then invoke `/study-pack-builder`.

## License

MIT. See `LICENSE`.
