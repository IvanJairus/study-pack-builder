# Verification

## Rule

Do not claim completion from a successful build alone. Verify the state, not the HTTP status. Save the command and its result.

## Source coverage

- Every slide/page appears in the coverage map.
- Every audio session has a transcript or a documented reason for omission.
- Every output page has a source range.

## Question bank

```bash
python scripts/check_site.py --root output --quiz output/assets/js/quiz-data.js --pdf output/bank-soal/question-bank.pdf
```

Check:

- Unique IDs.
- Four options per question.
- Answer exists among the options.
- Explanation and trap are non-empty.
- Every raw question ID appears exactly once.
- Frequency matches the source count.
- PDF question count matches the JSON.

## Site

```bash
python scripts/check_site.py --root output
```

Check:

- Zero broken relative links. Strip `?query` and `#hash` before testing the path.
- All pages have one `h1`.
- CSS and JS are versioned when changed.
- No dead buttons.
- Quiz filters, search, shuffle, check, retry, list mode, and progress persistence.
- Abbreviation tooltip on hover, keyboard focus, and tap.
- No tooltips inside quiz options and reference tables.
- Mobile 390 px and desktop 1440 px.
- No horizontal overflow except intentional table wrappers.
- No console errors.

## Artifacts

- Search for em dash as a sentence connector.
- Search for unintended CJK characters with Python, not a shell regex.
- Check JavaScript syntax with `node --check`.
- Verify print PDF opens and has the expected page count.
- Verify video with `ffprobe`, frame extraction, and a short speech-to-text sample.

## Acceptance table

| Area | Required evidence |
|---|---|
| Source | coverage map complete |
| Questions | 120 raw, 70 unique, every ID mapped once |
| Answers | 0 missing, 0 not in options |
| Site | 0 broken links, 0 console errors |
| Mobile | 390 px screenshot checked |
| Desktop | 1440 px screenshot checked |
| PDF | opens, question count matches |
| Video | duration, audio, frames, SRT |
| Distribution | no private source files in repo |

## Red flags

- A question with no explanation.
- A cluster that merged two different asks.
- A count that is copied from a previous version.
- A link checker that ignores query strings.
- A quiz that changes order on every render.
- A tooltip that blocks option clicks.
- A video that is silent or has the wrong language.
- A public repository containing source PDFs, audio, screenshots, names, or logos.
