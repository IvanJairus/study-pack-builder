# Delivery Gates

## Rule

A study pack is not ready because the pages look finished. It is ready only when every requested output exists, the brief is confirmed, the source inventory is complete, the map validates, every topic page has the learning blocks, and abbreviations come from one source.

Run the gate before delivery:

```bash
python scripts/check_site.py \
  --root output \
  --brief output/sumber/project-brief.json \
  --quiz output/assets/quiz-data.js \
  --pdf output/bank-soal/question-bank.pdf \
  --min-topics 5 \
  --strict
```

If the command fails, fix the pack. Do not report completion.

## Mandatory files

| File | Purpose |
|---|---|
| `sumber/project-brief.json` | Choices and explicit confirmation |
| `sumber/source-inventory.json` | SSOT, roles, hashes, support status |
| `sumber/coverage-map.md` | Source ref to output page |
| `map.html` | Full study map |
| `assets/map-data.js` | Category weights, matrix, route, relationships |
| `assets/map.js` | Renders map views |
| `assets/abbreviations.js` | Generated tooltip dictionary |
| `index.html` | Entry point with a compact map |
| `bank-soal.html` and `assets/quiz-data.js` | Quiz |
| `bank-soal/question-bank.pdf` | Print bank when requested |
| `interview.html` | Interview guide when requested |
| `sumber/transcripts/` | Transcripts when requested |
| `video/*.mp4` | Video when requested |

## Confirmation gate

Do not extract or build until the user confirms the brief.

1. Fill `sumber/project-brief.json`.
2. Show a compact MAKE SURE summary in chat: SSOT, source count, requested outputs, language, theme, video, transcripts, privacy.
3. Wait for an explicit yes. If the agent has a structured question tool, use it.
4. Run:

```bash
python scripts/confirm_brief.py sumber/project-brief.json --by "user" --note "confirmed in chat"
```

The gate rejects a brief without `confirmed_at` and `confirmed_by`.

## Source inventory and SSOT

```bash
python scripts/source_inventory.py sources/ \
  --out sumber/source-inventory.json \
  --brief sumber/project-brief.json \
  --normalized working/normalized.summary.json
```

The inventory records:

- `path`, `format`, `size`, `sha256`
- `role`: `primary`, `assessment`, `secondary`, or `ignored`
- `supported` and the adapter
- `ssot`: the authoritative source files
- ignored files and unsupported files with reasons

`brief.ssot` is a list of path or glob patterns. If it is omitted, all primary files become the SSOT. A declared SSOT that matches no file is an error. The inventory makes it possible to answer what was read, what was ignored, and which file wins when sources conflict.

## Map schema

`assets/map-data.js` defines `window.STUDY_MAP`:

```js
window.STUDY_MAP = {
  title: "Study map",
  subtitle: "How to move through the pack.",
  process: ["Identify", "Measure", "Monitor", "Respond"],
  topics: [
    {
      slug: "liquidity",
      kind: "topic",
      title: "Liquidity",
      page: "topic-03-liquidity.html",
      scope: "Short-term and structural funding risk.",
      weight: 20,
      source: "Slides 126-161",
      quiz_topic: "Liquidity",
      prerequisites: ["foundation"],
      accent: "#34567f",
      matrix: {
        Identify: "Cash-flow gaps",
        Measure: "LCR and NSFR",
        Monitor: "EWI and stress",
        Respond: "Funding plan"
      }
    }
  ],
  relationships: [
    { from: "Credit", to: "Liquidity", mechanism: "Defaults reduce cash inflow." }
  ],
  route: [
    { title: "Foundation", detail: "Start here.", page: "foundation.html", minutes: 20 }
  ]
};
```

Rules:

- 5 to 8 topic categories plus a foundation page for a real pack.
- Weights are positive and sum to 100.
- Every `page` exists.
- Every matrix step has a non-empty value.
- Every prerequisite points to a known slug.
- Every `quiz_topic` matches the quiz data and has at least one question.
- The route covers reading, practice, and interview.
- `index.html` has `data-topic-map` and a compact map.
- `map.html` has overview, matrix, route, and relationships views.

The map is not decoration. It decides what to study first, how much weight a category deserves, and where practice volume comes from.

## Topic page structure

Every page listed in the map must contain:

| Attribute | Required |
|---|---|
| `data-study-block="orientation"` | yes |
| `data-study-block="essentials"` | yes |
| `data-study-block="process"` | yes |
| `data-study-block="traps"` | yes |
| `data-study-block="self-check"` | yes |
| `data-source-range="..."` | yes |
| `data-study-block="definition"` | recommended |
| `data-study-block="parameters"` | recommended |
| `data-study-block="measurement"` | recommended |
| `data-study-block="monitoring"` | recommended |
| `data-study-block="reporting"` | recommended |

The recommended blocks make a page stronger, but the strict gate enforces the core learning loop: orientation, essentials, process, traps, self-check, and source range. A self-check block must contain at least one `<details>` element. Each page needs one `h1` and at least two `h2` sections.

## Abbreviation single source

The visible table in `reference.html` is the source of truth. Every row has `data-abbr-row`.

```bash
python scripts/build_abbreviations.py
python scripts/build_abbreviations.py --check
```

The generated `assets/abbreviations.js` is loaded before `site.js` on every page. `site.js` reads `window.ABBREVIATIONS`; do not keep a second hardcoded dictionary. The gate also warns when a frequent acronym in the content is missing from the dictionary. Put local organization names or Roman numerals that should not get tooltips in `assets/abbreviations.ignore`, one token per line.

## Gate table

| Gate | Pass condition |
|---|---|
| Brief | Confirmed, complete, requested outputs exist |
| Inventory | SSOT present, hashes valid, every role valid |
| Map | Categories, weights, matrix, pages, links |
| Structure | Core blocks and source range on every topic page |
| Abbreviations | Generated file matches the table and is used by site.js |
| Coverage | `sumber/coverage-map.md` exists and has a table |
| Transcripts | Present when the brief requests them |
| Quiz | Schema passes with 0 errors |
| Links | 0 broken relative links |
| Artifacts | No em dash or unintended CJK |
| PDF | Question count matches when checked |

## Stop conditions

Stop and ask the user when:

- The brief is not confirmed.
- The SSOT is missing or ambiguous.
- A requested output cannot be built.
- Transcripts are requested but the audio is missing.
- A topic page cannot fill a required learning block from the source.

Report the blocker. Do not silently drop an output or fill a gap by guessing.
