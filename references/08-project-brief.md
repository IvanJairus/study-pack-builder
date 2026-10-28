# Project Brief

## Goal

Collect the choices that change the output structure once, before extraction starts. Do not ask the same question again in later phases.

## Question list

Ask these in one batch. Accept defaults when the user does not care.

1. **Sources and output:** Which folder contains the PDFs, PPTX, audio, and question files? Where should the study pack be written?
2. **Exam shape:** How many questions, how many minutes, which question types, and is there an interview?
3. **Language:** Which language should the summaries, quiz, and video use?
4. **Outputs:** Which outputs do you want: website, quiz, printable PDF, narrated video, interview guide, and transcripts?
5. **Video:** If yes, how many minutes, which voice, and do you want subtitles?
6. **Theme:** Light, dark, or system? Keep the default light if the user is unsure.
7. **Audio and exclusions:** May the recordings be transcribed? Which files or formats should be ignored?
8. **Distribution:** Public or private? Are there confidentiality, naming, or attribution constraints?

## Defaults

| Field | Default |
|---|---|
| Language | Source language |
| Theme | Light |
| Question types | Infer from the source; mixed types allowed |
| Video | Off unless requested |
| Video length | 5 minutes when enabled |
| Print PDF | On |
| Quiz | On |
| Interview guide | On if the exam includes an interview |
| Transcripts | On when audio is transcribed |
| Site | Offline, no CDN |

## Brief schema

```json
{
  "goal": "exam preparation",
  "sources": "./sources",
  "output": "./study-pack",
  "language": "id",
  "exam": {
    "questions": 30,
    "minutes": 45,
    "question_types": ["single_choice", "multiple_choice", "true_false", "short_answer"],
    "interview": true
  },
  "outputs": {
    "website": true,
    "quiz": true,
    "print_pdf": true,
    "video": false,
    "interview_guide": true,
    "transcripts": true
  },
  "theme": {
    "mode": "light",
    "accent": "green",
    "offline": true
  },
  "video": {
    "enabled": false,
    "minutes": 5,
    "voice": "Damayanti",
    "language": "id",
    "subtitles": true
  },
  "audio": {
    "transcribe": true,
    "notes": "exam advice only"
  },
  "ignore": ["diagrams", "legacy HTML"],
  "constraints": ["no proprietary content in public examples"]
}
```

Use `assets/project-brief.example.json` as a copyable starting point.

## How to use the brief

1. Read the brief before inventory.
2. If a required field is missing, ask one short question.
3. Write the brief into the output folder as `sumber/project-brief.json` for traceability.
4. Build only the outputs marked `true`.
5. Skip video scripting, TTS, slides, and rendering when `outputs.video` is false.
6. Skip the print PDF when `outputs.print_pdf` is false.
7. Set the site `data-mode` to the chosen theme.
8. At the end, report which optional outputs were intentionally skipped.

## Theme modes

- `light`: white reading surface, dark ink.
- `dark`: dark reading surface, light ink. Check contrast in every state: normal text, muted text, borders, callouts, quiz correct and wrong states, tooltip, and focus ring.
- `system`: follow `prefers-color-scheme` at build time. If the output must stay static, choose light or dark explicitly.

The starter template supports both `light` and `dark` through the `data-mode` attribute on `<body>` and a toggle in the top bar. The brief decides the initial mode.

## Video decision

Do not generate a video by default. It adds minutes of rendering time and a synthetic voice. Ask first. If the answer is no, keep the script and the site. If the answer is yes, confirm duration and voice, then run the video pipeline.
