---
name: study-pack-builder
description: Build a complete study pack from mixed local sources such as PDF or PPTX slides, audio recordings, and question banks. Use when the user wants a structured study website, a deduplicated exam question bank with explanations, a printable PDF, a narrated overview video, interview notes, or a repeatable source-to-study-pack pipeline with verification.
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

## Inputs to collect

Ask at most three questions. Otherwise use sensible defaults.

- Source folder and output folder.
- Exam format, language, and whether interview preparation is required.
- Whether audio may be transcribed and how long the narrated video should be.
- Brand/theme constraints and whether the result must work offline.
- Whether the user wants a public or private distribution.

Default assumptions: Indonesian or the source language, offline static site, white theme, 5-minute video, local processing only.

## Workflow

### 1. Inventory and extract

Create a source inventory before writing content.

- List file types, counts, pages, durations, and whether text is selectable.
- Extract PDF text per page with `scripts/extract_pdf.py`.
- Extract PPTX text and speaker notes with `python-pptx`.
- OCR image-only PDFs and screenshots with `scripts/ocr.sh` on macOS Vision, or Tesseract elsewhere.
- Transcribe audio with `mlx-whisper` on Apple Silicon, or `whisper.cpp`/`faster-whisper` elsewhere.
- Convert SRT to readable timestamped paragraphs with `scripts/srt_to_paragraphs.py`.
- Keep raw extraction in a working directory, never in the final deliverable.

Read `references/01-source-extraction.md` for commands, fallbacks, and failure modes.

### 2. Derive the study architecture

Derive topics from the source, not from a fixed template.

- Group material into 5 to 8 major clusters plus a foundation/orientation page.
- Build one matrix: clusters x the source's recurring process (for example identify, measure, monitor, communicate).
- Add a relationship map for cross-topic effects.
- Map every slide/page range to exactly one output page.
- Identify cross-cutting themes such as regulation, climate, cyber, or reporting.

Read `references/03-content-architecture.md` for page structure and coverage mapping.

### 3. Build the question bank

1. Extract questions and options from PDFs. If answers are highlighted, detect the highlight rectangles and map them to option lines with `scripts/extract_questions.py`.
2. Cross-check with other question sources such as forms, answer keys, or screenshots.
3. Fill missing keys only from duplicates. Keep a list of unresolved items.
4. Normalize text, cluster duplicates with `scripts/dedup_questions.py`, and choose one canonical wording per cluster.
5. Preserve every raw question ID in the cluster members. Every raw question must appear exactly once.
6. Write an explanation for every unique question: why the key is right, why the main distractors are wrong, and the exam trap. Ground explanations in the source material.
7. Validate that every answer exists among the options and that every question has four options.

Read `references/02-question-bank.md` for the schema, heuristics, and validation rules.

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

Build all outputs from one data model where possible.

- Website: static, offline, white theme, system fonts, responsive, no CDN.
- Quiz: filter by topic, search, shuffle, reveal answer, explanation, trap, retry wrong, list mode, local progress.
- Print PDF: a print stylesheet with all questions, keys, and explanations, rendered with headless Chrome.
- Video: 5 minutes, narrated TTS, screenshots of the site, title/bullets/takeaway, SRT.
- Reference pages: glossary, abbreviations with tooltips, coverage map.

Read `references/04-site-build.md` and `references/05-video.md` before implementing.

### 7. Verify and deliver

Run all checks:

- Every source page/slide is mapped to an output page.
- Every raw question is mapped exactly once.
- Every answer is in the options, four options per question, explanation and trap present.
- Zero broken relative links.
- Quiz interactions work on desktop and mobile.
- No console errors.
- White theme renders correctly at 390 px and 1440 px.
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
| Source coverage | Every page/slide has a destination or is explicitly marked as non-content |
| Question coverage | Every raw question ID appears once in a cluster |
| Answer integrity | Answer is one of the options; four options; no blank explanation |
| Site integrity | 0 broken links; 0 console errors; quiz tested |
| Responsive | 390 px and 1440 px checked; no horizontal overflow except intentional tables |
| Print | PDF opens; expected question count; readable at A4 |
| Video | Duration matches target; audio audible; frames match sections; SRT valid |
| Distribution | No source PDFs, audio, screenshots, personal data, or logos in the public repo |

## Resources

- `scripts/extract_pdf.py`: text per page and TOC.
- `scripts/extract_questions.py`: highlighted answers to structured JSON.
- `scripts/dedup_questions.py`: fuzzy clustering and canonical questions.
- `scripts/ocr_vision.swift` and `scripts/ocr.sh`: macOS Vision OCR.
- `scripts/srt_to_paragraphs.py`: timestamped readable transcripts.
- `scripts/tts_say.py`: macOS TTS for video narration.
- `scripts/make_slides.py`: white-theme 1920x1080 slides from a script JSON.
- `scripts/render_video.py`: segments, intro/outro, concat, AAC/H.264.
- `scripts/check_site.py`: links, quiz data, PDF count, artifact scan.
- `references/`: detailed procedures and guardrails.
- `assets/site-template/`: offline study-site starter.
- `assets/video-template/script.example.json`: video script schema.
- `examples/synthetic/`: safe test data.

## Install

Clone this repository into a skill directory:

```bash
git clone https://github.com/IvanJairus/study-pack-builder.git \
  ~/.qoder/skills/study-pack-builder
```

Or copy it into a project-level skill directory:

```bash
git clone https://github.com/IvanJairus/study-pack-builder.git \
  .qoder/skills/study-pack-builder
```

Reload skills, then invoke `/study-pack-builder`.

## License

MIT. See `LICENSE`.
