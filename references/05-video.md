# Narrated Video

## Goal

Produce a short overview that carries the big points and sends the learner to the website for detail. Five minutes is a good default.

## Structure

| Section | Time | Content |
|---|---|---|
| Intro | 20-25s | What the pack covers, what the video does not cover |
| Framework | 25-35s | Shared concepts and process |
| Topic 1-6 | 20-30s each | One core idea, one formula, one trap |
| Question bank | 25-30s | Dedup count, priority questions, how to practice |
| Interview | 25-30s | What is assessed, answer structure |
| Close | 25-35s | Study route, page names, disclaimer |

## Script

Target about 700 words for five minutes. Write short sentences. Say numbers in words when TTS may misread them.

Example:

> "Liquidity coverage ratio equals high quality liquid assets divided by net cash outflow. The minimum is one hundred percent for a thirty day stress period."

Measure the generated audio, not the word count. Adjust the speaking rate or trim the script.

## TTS

On macOS, list available voices:

```bash
say -v '?' | grep -i indonesian
```

Generate one file per section:

```bash
say -v Damayanti -r 170 -o working/audio/intro.aiff "Narration text."
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 working/audio/intro.aiff
```

Or use `scripts/tts_say.py`:

```bash
python scripts/tts_say.py working/script.json --voice Damayanti --rate 170
```

The script updates each section with its measured duration.

Cross-platform alternatives: Piper, ElevenLabs, Azure Speech, or any TTS that outputs WAV/AIFF. Keep the same per-section file layout.

## Slides

Use 1920x1080. White background, dark text, one accent per section.

Layout:

- Left: section number, title, two or three bullets, takeaway.
- Right: screenshot of the relevant website page in a browser-like card.
- Bottom: detail label and progress.

Use `scripts/make_slides.py` with a JSON script and screenshots.

```bash
python scripts/make_slides.py working/script.json --shots working/shots --out working/slides
```

Keep text large enough for mobile viewing. Do not put a full paragraph on a slide.

The video slides are white by default. If the brief asks for a dark video, change the slide palette and re-check text contrast. The website dark mode does not apply to the rendered slides automatically.

## Render

For each section:

- Loop the slide image for the audio duration.
- Use H.264, yuv420p, 30 fps, AAC 192 kbps.
- Add a short intro and outro hold with silence.
- Concatenate with the concat demuxer.

```bash
python scripts/render_video.py working/script.json \
  --slides working/slides --audio working/audio --out working/final/overview.mp4
```

The script prints the final duration. Verify with `ffprobe`.

## Subtitles

Split narration into sentences. Allocate time proportionally to character count. Write SRT with `HH:MM:SS,mmm` timestamps.

Check:

- Cue count.
- Last cue end matches video duration.
- No empty cue.
- No cue longer than two lines on screen.

## Quality checks

- Duration within 2 percent of target.
- Audio mean volume around -17 dB, peak below -1 dB.
- Frame at each section start matches the intended slide.
- Speech-to-text spot check confirms the language and key terms.
- No proprietary screenshots, names, or logos in public examples.
- TTS disclosure in the video description or the site footer.
