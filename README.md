# Study Pack Builder

A reusable agent skill that turns a folder of study material into a verified study pack: a structured website, a deduplicated question bank, a printable PDF, a narrated overview video, and interview notes.

The source slides and PDFs are the authority. Audio is used for emphasis and advice, not as the primary material. Every output is traceable to a source range.

## Quick start

The installer detects which AI apps you already have and installs the skill into each one:

```bash
npx github:IvanJairus/study-pack-builder
```

Check what it sees first:

```bash
npx github:IvanJairus/study-pack-builder --list
```

The short form below requires the package to be published to npm. It is prepared but not published yet:

```bash
npx study-pack-builder
```

### Supported agents

| Agent | Detected config | User-level install path |
|---|---|---|
| Qoder | `~/.qoder` | `~/.qoder/skills/study-pack-builder` |
| Claude Code | `~/.claude` | `~/.claude/skills/study-pack-builder` |
| Cursor | `~/.cursor` | `~/.cursor/skills/study-pack-builder` |
| Antigravity | `~/.gemini/antigravity` | `~/.gemini/antigravity/skills/study-pack-builder` |
| Codex | `~/.codex` | `~/.codex/skills/study-pack-builder` |

Only detected apps are touched by default. If nothing is detected, the installer stops and explains the flags instead of guessing. WorkBuddy AI is detected only to print a manual note, because it has no documented skills folder.

Project-level install writes into the config folders present in the current directory, for example `./.qoder/skills/study-pack-builder`:

```bash
npx github:IvanJairus/study-pack-builder --project
```

Manual fallback for any agent:

```bash
git clone https://github.com/IvanJairus/study-pack-builder.git \
  ~/.qoder/skills/study-pack-builder
```

Then reload skills and invoke:

```text
/skills reload
/study-pack-builder
```

Installer options:

| Option | Meaning |
|---|---|
| `--list` | Show detected agents and paths, then exit |
| `--all` | Install to every supported agent path, even if not detected |
| `--agent <ids>` | Install only to comma-separated ids, e.g. `claude,cursor` |
| `--project` | Install to project-level config folders in the current directory |
| `--target <path>` | Install to a custom directory |
| `--force` | Back up an existing install and replace it |
| `--dry-run` | Print the plan without writing |
| `--help` | Show help |

Existing installs are skipped unless `--force` is passed. A forced update moves the old copy to `~/.study-pack-builder/backups/<agent>-<timestamp>` before writing.

## Inputs

Give the agent a source folder and a target output folder. A typical source folder looks like this:

```text
sources/
├── material.pdf
├── material.pptx
├── notes.docx
├── summary.md
├── session-1.m4a
├── session-2.m4a
└── questions/
    ├── answer-key-1.pdf
    ├── answer-key-2.pdf
    ├── bank.xlsx
    ├── forms-score.pdf
    └── screenshots/
        ├── question-01.png
        └── question-02.png
```

Supported text formats:

| Format | Handled by |
|---|---|
| PDF, PPTX | Dedicated extractors, with PyMuPDF and python-pptx |
| TXT, Markdown, HTML, EPUB | `normalize_source.py`, no extra dependencies |
| DOCX, CSV, TSV, XLSX | `normalize_source.py`, read from the document XML |
| DOC, RTF | `normalize_source.py` through `textutil` or LibreOffice |
| PNG, JPG, scanned PDF | OCR with `ocr.sh` or Tesseract |
| M4A, MP3, WAV, MP4 | Whisper transcription |

The normalizer writes one JSONL stream with refs such as `paragraph:12`, `row:7`, `sheet:Liquidity!row:7`, and `chapter:2!line:8-10`. See [references/09-format-adapters.md](references/09-format-adapters.md).

Useful facts to provide:

1. Exam format and number of questions.
2. Language of the study pack.
3. Whether interview preparation is required.
4. Desired video length and whether audio may be transcribed.
5. Brand or theme constraints, especially whether the site must work offline.
6. Which files to ignore, such as diagrams, old HTML exports, or duplicate compressed audio.

Example prompt:

```text
Use study-pack-builder on ./sources. Write the output to ./study-pack.
The exam has 30 multiple-choice questions plus a 30-minute interview.
Use Indonesian. Theme: dark. Skip the video for now.
Build the quiz and the print PDF. Ignore diagrams and old HTML.
```

## Project brief

The skill asks for a short brief before extraction. Start from [assets/project-brief.example.json](assets/project-brief.example.json).

| Choice | Default |
|---|---|
| `theme.mode` | `light`, or `dark` / `system` |
| `exam.question_types` | Inferred from source; mixed types allowed |
| `outputs.website` | `true` |
| `outputs.quiz` | `true` |
| `outputs.print_pdf` | `true` |
| `outputs.video` | `false` unless requested |
| `video.minutes` | `5` when enabled |
| `outputs.interview_guide` | `true` when the exam has an interview |
| `outputs.transcripts` | `true` when audio is transcribed |
| `language` | Source language |

If video is off, the agent skips scripting, TTS, slides, and rendering. If dark is selected, the template uses `data-mode="dark"` and the top bar still offers a light/dark toggle.

## Outputs

The skill produces a folder like this:

```text
study-pack/
├── index.html
├── map.html
├── foundation.html
├── topic-01.html ... topic-0N.html
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

What each output is for:

| Output | Purpose |
|---|---|
| `index.html` | Entry point, topic map, study route |
| `topic-*.html` | One page per major topic, with definitions, tables, formulas, traps, and self-check |
| `bank-soal.html` | Interactive quiz with filters, search, shuffle, answer reveal, explanations, and retry-wrong |
| `question-bank.pdf` | Printable question bank with keys and explanations |
| `interview.html` | Interview questions, model answers, and instructor advice |
| `video/overview.mp4` | Short narrated overview, only when requested |
| `sumber/coverage-map.md` | Source-to-page coverage table |
| `sumber/transcripts/` | Machine-generated transcripts with timestamps |

## Question types

The quiz and validator support four types:

| Type | Options | Answer |
|---|---|---|
| `single_choice` | 2 or more | One option key |
| `multiple_choice` | 2 or more | Array of at least 2 keys |
| `true_false` | None | Boolean |
| `short_answer` | None | `accepted_answers` array |

A missing type is treated as `single_choice` for older banks. Validate any data file with:

```bash
python scripts/quiz_schema.py assets/js/quiz-data.js
```

See [examples/synthetic/questions-flexible.json](examples/synthetic/questions-flexible.json) for a complete sample.

## Workflow

1. **Inventory and extract** mixed formats with `normalize_source.py`, PDF/PPTX text, OCR screenshots, and audio transcripts.
2. **Derive architecture** into 5 to 8 topic clusters, a process matrix, and a coverage map.
3. **Build the question bank**: extract questions, detect highlighted keys, cross-check duplicates, deduplicate by type, and write explanations.
4. **Extract audio advice** and group it by theme with session timestamps.
5. **Write content** in a consistent page template: essentials, process, details, traps, self-check, source.
6. **Build outputs**: static site, quiz, print PDF, video, SRT.
7. **Verify**: links, answers, counts, responsive layout, quiz interactions, PDF, video, and source coverage.

## Requirements

| Tool | Why |
|---|---|
| Python 3.10+ | Scripts |
| `pip install -r requirements.txt` | PyMuPDF, python-pptx, Pillow for PDF/PPTX/video |
| `ffmpeg` and `ffprobe` | Video and audio |
| Node.js 18+ | npx installer only |
| macOS Vision + `say` | Optional OCR and TTS on macOS |
| `mlx-whisper` or Whisper.cpp | Audio transcription |
| LibreOffice or `textutil` | Legacy DOC/RTF conversion; `textutil` ships with macOS |

The text formats TXT, Markdown, HTML, DOCX, EPUB, CSV, TSV, and XLSX use only the Python standard library. PDF and PPTX need PyMuPDF or python-pptx.

## Scripts

| Script | Use |
|---|---|
| `scripts/normalize_source.py` | Mixed formats to JSONL with source refs and a summary |
| `scripts/extract_pdf.py` | Text per page and TOC |
| `scripts/extract_questions.py` | Questions and highlighted answers from PDF, A to H |
| `scripts/dedup_questions.py` | Type-aware fuzzy clustering and answer conflict flags |
| `scripts/quiz_schema.py` | Validate four question types, options, answers, and explanations |
| `scripts/ocr.sh` | macOS Vision OCR |
| `scripts/srt_to_paragraphs.py` | Readable timestamped transcripts |
| `scripts/tts_say.py` | macOS TTS and duration measurement |
| `scripts/make_slides.py` | White-theme 1920x1080 slides |
| `scripts/render_video.py` | Segments, intro/outro, concat, H.264/AAC |
| `scripts/check_site.py` | Links, quiz schema, PDF count, artifact scan |

Example checks:

```bash
python scripts/check_site.py \
  --root output \
  --quiz output/assets/js/quiz-data.js \
  --pdf output/bank-soal/question-bank.pdf
```

Run the repository tests:

```bash
npm test
```

The test suite covers the four question types, type-aware deduplication, answer conflicts, XML safety, and normalization for TXT, Markdown, HTML, DOCX, EPUB, CSV, and XLSX.

## Guardrails

- Do not commit source PDFs, audio, screenshots, personal data, or organization logos to a public repository.
- Keep the official source as the authority. If a key is missing, mark it unresolved instead of guessing.
- Audio is complementary. Slides and PDFs win when sources conflict.
- Use synthetic examples for tests and documentation.
- Do not help bypass an exam or leak live exam content.

## Repository layout

```text
study-pack-builder/
├── SKILL.md
├── README.md
├── LICENSE
├── package.json
├── bin/cli.js
├── scripts/
├── references/
│   ├── 01-source-extraction.md ... 07-guardrails.md
│   ├── 08-project-brief.md
│   └── 09-format-adapters.md
├── assets/
│   ├── project-brief.example.json
│   ├── site-template/
│   └── video-template/
└── examples/
    └── synthetic/
```

The installed skill does not copy `package.json`, `bin/`, or this README. It copies `SKILL.md` and the reusable resources only.

## Bahasa Indonesia

Jalankan `npx github:IvanJairus/study-pack-builder`, lalu gunakan `/study-pack-builder`. Input berupa folder campuran PDF, PPTX, DOCX, TXT, Markdown, HTML, EPUB, CSV, XLSX, audio, dan soal. Output berupa website belajar, bank soal empat tipe, PDF, video bersuara, dan peta cakupan sumber.

## License

MIT. See [LICENSE](LICENSE).
