# Verification

## Rule

Do not claim completion from a successful build alone. Verify the state, not the HTTP status. Save the command and its result.

## Source coverage

- Every slide, page, paragraph, line range, and table row appears in `coverage.json` as covered, non-content, or unresolved.
- Every raw question ID appears exactly once in the final quiz.
- Every audio session has a transcript or a documented reason for omission.
- Every output page has a source range or normalized ref.

```bash
python scripts/check_coverage.py --coverage output/sumber/coverage.json --root output --quiz output/assets/quiz-data.js
```

## Delivery gate

```bash
python scripts/check_site.py \
  --root output \
  --brief output/sumber/project-brief.json \
  --quiz output/assets/quiz-data.js \
  --pdf output/bank-soal/question-bank.pdf \
  --min-topics 5 \
  --strict
```

The gate must pass before delivery. It checks the brief, inventory, map, page structure, abbreviations, coverage, transcripts, quiz, links, and artifacts. Read `references/10-delivery-gates.md` for the failure conditions.

## Question bank

```bash
python scripts/quiz_schema.py output/assets/quiz-data.js
```

Check:

- Unique IDs and a non-empty topic for every question.
- At least two options for choice questions, with uppercase keys.
- Single answer is in the options; multiple answer is an array of at least two valid keys.
- True or false answer is a boolean.
- Short answer has at least one accepted variant.
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
- Single choice, multiple choice, true or false, and short answer all work.
- Multiple choice requires the exact set; short answer accepts listed variants.
- The map renders layers, category magnitude, a spoiler concept tree, matrix, route, and relationships at 390 px and 1440 px.
- Every map category links to an existing page with a source range.
- Tooltips resolve from `assets/abbreviations.js`, and the reference search works.
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
| Brief | confirmed_at and confirmed_by present; requested outputs exist |
| Source | inventory SSOT, coverage map, and coverage.json complete |
| Questions | raw and unique counts match the cluster output; every ID mapped once |
| Answers | 0 missing, 0 not in options, 0 invalid type |
| Map | layers, magnitude, big ideas, concepts, connections; weights sum to 100; pages exist |
| Structure | core blocks and source range on every topic page; recommended blocks reviewed |
| Abbreviations | generated file matches the table; search works |
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
