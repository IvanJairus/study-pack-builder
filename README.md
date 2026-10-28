# Study Pack Builder

A reusable agent skill that turns a folder of study material into a verified study pack: a structured website, a deduplicated question bank, a printable PDF, a narrated overview video, and interview notes.

The source slides and PDFs are the authority. Audio is used for emphasis and advice, not as the primary material. Every output is traceable to a source range.

## Quick start

Install the skill with npx:

```bash
npx github:IvanJairus/study-pack-builder
```

Project-level install:

```bash
npx github:IvanJairus/study-pack-builder --project
```

The short form below requires the package to be published to npm. It is prepared but not published yet:

```bash
npx study-pack-builder
```

Manual fallback:

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
| `--project` | Install to `./.qoder/skills/study-pack-builder` |
| `--target <path>` | Install to a custom directory |
| `--force` | Back up an existing install and replace it |
| `--dry-run` | Print the plan without writing |
| `--help` | Show help |

## Inputs

Give the agent a source folder and a target output folder. A typical source folder looks like this:

```text
sources/
├── material.pdf
├── material.pptx
├── session-1.m4a
├── session-2.m4a
└── questions/
    ├── answer-key-1.pdf
    ├── answer-key-2.pdf
    ├── forms-score.pdf
    └── screenshots/
        ├── question-01.png
        └── question-02.png
```

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

## Workflow

1. **Inventory and extract** PDF/PPTX text, OCR screenshots, and transcribe audio.
2. **Derive architecture** into 5 to 8 topic clusters, a process matrix, and a coverage map.
3. **Build the question bank**: extract questions, detect highlighted keys, cross-check duplicates, deduplicate, and write explanations.
4. **Extract audio advice** and group it by theme with session timestamps.
5. **Write content** in a consistent page template: essentials, process, details, traps, self-check, source.
6. **Build outputs**: static site, quiz, print PDF, video, SRT.
7. **Verify**: links, answers, counts, responsive layout, quiz interactions, PDF, video, and source coverage.

## Requirements

| Tool | Why |
|---|---|
| Python 3.10+ | Scripts |
| `pip install -r requirements.txt` | PyMuPDF, python-pptx, Pillow |
| `ffmpeg` and `ffprobe` | Video and audio |
| Node.js 18+ | npx installer only |
| macOS Vision + `say` | Optional OCR and TTS on macOS |
| `mlx-whisper` or Whisper.cpp | Audio transcription |

## Scripts

| Script | Use |
|---|---|
| `scripts/extract_pdf.py` | Text per page and TOC |
| `scripts/extract_questions.py` | Questions and highlighted answers from PDF |
| `scripts/dedup_questions.py` | Fuzzy clustering and canonical questions |
| `scripts/ocr.sh` | macOS Vision OCR |
| `scripts/srt_to_paragraphs.py` | Readable timestamped transcripts |
| `scripts/tts_say.py` | macOS TTS and duration measurement |
| `scripts/make_slides.py` | White-theme 1920x1080 slides |
| `scripts/render_video.py` | Segments, intro/outro, concat, H.264/AAC |
| `scripts/check_site.py` | Links, quiz data, PDF count, artifact scan |

Example checks:

```bash
python scripts/check_site.py \
  --root output \
  --quiz output/assets/js/quiz-data.js \
  --pdf output/bank-soal/question-bank.pdf
```

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
│   └── 08-project-brief.md
├── assets/
│   ├── project-brief.example.json
│   ├── site-template/
│   └── video-template/
└── examples/
    └── synthetic/
```

The installed skill does not copy `package.json`, `bin/`, or this README. It copies `SKILL.md` and the reusable resources only.

## Bahasa Indonesia

Jalankan `npx github:IvanJairus/study-pack-builder`, lalu gunakan `/study-pack-builder`. Input berupa folder PDF/PPTX, audio, dan soal. Output berupa website belajar, bank soal, PDF, video bersuara, dan peta cakupan sumber.

## License

MIT. See [LICENSE](LICENSE).
