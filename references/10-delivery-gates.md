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
| `sumber/coverage-map.md` | Human-readable source ref to output page |
| `sumber/coverage.json` | Machine-readable coverage audit |
| `map.html` | Full study map |
| `assets/map-data.js` | Layers, category magnitude, big ideas, concepts, matrix, route, relationships |
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
  subtitle: "Read from the outside in.",
  layers: [
    { id: "outer", title: "Outer layer", description: "Categories and magnitude." },
    { id: "middle", title: "Big ideas", description: "The main points." },
    { id: "inner", title: "Details", description: "Concepts and traps." },
    { id: "practice", title: "Practice", description: "Questions and interview." }
  ],
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
      magnitude: { slides: 36, concepts: 9, formulas: 2, minutes: 20 },
      big_ideas: [
        {
          title: "Three dimensions",
          summary: "Profile, short-term, and long-term adequacy.",
          weight: 30,
          concepts: [
            { title: "LCR", gist: "HQLA divided by net cash outflow.", formula: "LCR = HQLA / NCO", source: "Slide 142-148" },
            { title: "NSFR", gist: "ASF divided by RSF.", formula: "NSFR = ASF / RSF", source: "Slide 148-154" }
          ]
        }
      ],
      connections: [
        { to: "credit", relation: "affected by", mechanism: "Defaults reduce cash inflow." }
      ],
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
- At least three layers, each with a title and description.
- Category weights are positive and sum to 100.
- Every `page` exists.
- Every matrix step has a non-empty value.
- Every category has a magnitude with positive slides and concepts, and a non-negative formula count.
- Every category has at least two big ideas. Their weights sum to 100.
- Every big idea has at least two concepts. Each concept has a title, gist, and source.
- `magnitude.concepts` equals the total number of concepts in the category.
- Every connection target is a known slug and has a relation and mechanism.
- Every prerequisite points to a known slug.
- Every `quiz_topic` matches the quiz data and has at least one question.
- The route covers reading, practice, and interview.
- `index.html` has `data-topic-map` and a compact map.
- `map.html` has layers, overview, concepts, matrix, route, and relationships views.
- Big ideas are visible; concepts are collapsed by default, with a control to open all.

The map is not decoration. It is the spoiler: the learner reads the outer layer, opens a big idea, then reads the concepts only when needed.

## Coverage audit

`sumber/coverage.json` is the machine-readable audit. `coverage-map.md` is the readable companion.

Build a range-level manifest from the map:

```bash
python scripts/build_coverage.py \
  --out sumber/coverage.json \
  --map assets/map-data.js \
  --quiz assets/quiz-data.js \
  --source "source deck" \
  --question-source "question bank" \
  --audio "session-1.m4a" --audio "session-2.m4a"
```

Validate it:

```bash
python scripts/check_coverage.py \
  --coverage sumber/coverage.json \
  --root . \
  --quiz assets/quiz-data.js
```

For the strongest audit, add `--normalized working/normalized.jsonl` and set `level` to `unit`. Then every normalized record must appear exactly once in the manifest.

Schema:

```json
{
  "level": "range",
  "source_inventory": "sumber/source-inventory.json",
  "range_totals": [
    {"source": "deck.pptx", "kind": "slide_range", "total": 286}
  ],
  "units": [
    {
      "source": "deck.pptx",
      "ref": "Slide 1-37",
      "kind": "slide_range",
      "from": 1,
      "to": 37,
      "page": "foundation.html",
      "status": "covered"
    }
  ],
  "questions": {
    "raw_total": 120,
    "unique_total": 71,
    "raw_ids": ["S1-03"],
    "mapped_ids": ["S1-03"],
    "missing_ids": [],
    "duplicate_ids": []
  },
  "summary": {"total": 1, "covered": 1, "non_content": 0, "unresolved": 0}
}
```

Rules:

- Every unit status is `covered`, `non-content`, or `unresolved`.
- `covered` needs a page that exists.
- `non-content` needs a reason.
- `unresolved` is a delivery failure.
- Range units must not overlap or leave gaps.
- Every raw question ID appears exactly once in the final quiz.
- Every range family has a `range_totals` entry. Its ranges start at 1, have no gaps or overlaps, and end at the declared total.
- Every requested output and the source inventory must exist.
- A range manifest proves every declared range, not every individual unit. Use unit-level coverage when normalized JSONL exists.
- If `build_coverage.py` is run without `--raw-questions`, raw IDs are taken from the quiz sources. That checks internal uniqueness, not an external extraction. Pass `--raw-questions` for an external audit.

The gate runs the same validator with `check_site.py --brief ... --strict`.

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
| Map | Layers, categories, magnitude, big ideas, concepts, connections, pages, links |
| Structure | Core blocks and source range on every topic page |
| Abbreviations | Generated file matches the table and is used by site.js |
| Coverage | coverage.json validates; ranges have no gaps; raw questions mapped once |
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
