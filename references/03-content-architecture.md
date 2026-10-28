# Content Architecture

## Goal

Make a large source deck feel small. A learner should always know where they are, why a topic matters, and what to study next.

## Derive clusters

1. Read the source table of contents and section dividers.
2. Group sections into 5 to 8 major clusters. Use the source's own vocabulary.
3. Separate a foundation page for shared concepts, regulations, and frameworks.
4. Mark cross-cutting themes that appear in several clusters, such as climate, cyber, or reporting.
5. Build a matrix: clusters x the process used repeatedly in the source. Common processes are identify, measure, monitor, and communicate.
6. Build a relationship map for cross-topic effects, for example credit stress to liquidity.

Do not force six clusters if the source has five or nine. The structure must follow the material.

## Page template

Use a consistent order. Add the matching `data-study-block` attribute to each section so the delivery gate can verify it:

1. Kicker and title.
2. One-sentence orientation (`data-study-block="orientation"`).
3. "30-second essentials", three to five bullets (`data-study-block="essentials"`).
4. The process sequence as a visual (`data-study-block="process"`).
5. Definition and scope (`data-study-block="definition"`).
6. Factors or parameters in a table (`data-study-block="parameters"`).
7. Measurement methods and formulas (`data-study-block="measurement"`).
8. Monitoring and controls (`data-study-block="monitoring"`).
9. Reporting frequency and recipients (`data-study-block="reporting"`).
10. Exam traps (`data-study-block="traps"`).
11. Self-check questions (`data-study-block="self-check"`).
12. Source range (`data-source-range="Slides 1-20"`).

This order reduces memory load: the learner sees the big picture before the details. Items 1, 2, 4, 10, 11, and 12 are mandatory for every topic page. Items 5 to 9 are required by the strict delivery gate.

## Foundation page

Include:

- Purpose of the certification or exam.
- The shared framework and process.
- Governance roles and responsibilities.
- The list of topics and how they relate.
- Scoring and reporting cadence.
- Cross-cutting themes.
- A small glossary or link to one.

## Topic page

Use tables for parameters, methods, and reporting. Use formulas for ratios and capital calculations. Use one process visual and one relationship callout. Avoid long prose blocks.

Add a "traps" section. The most useful traps come from the question bank and the instructor's audio notes.

## Study map

Create `map.html` and a compact map on the index. The map is data-driven from `assets/map-data.js`, not hand-written cards.

The map has four layers:

1. Outer layer: categories, weights, source ranges, and magnitude.
2. Big ideas: the main points that define each category.
3. Details: concepts, definitions, formulas, traps, and source refs.
4. Practice: question volume and the route to the quiz and interview.

Each category declares:

- `title`, `slug`, `page`, `kind`
- `weight`: positive, all weights sum to 100
- `source`: slide, page, line, or row range
- `quiz_topic`: the topic name used by the quiz
- `prerequisites`: slugs that should be read first
- `magnitude`: slides, concepts, formulas, and minutes
- `big_ideas`: two to six main points, with weights summing to 100
- `connections`: target category, relation, and mechanism
- `matrix`: one non-empty value per process step

Each big idea declares a title, summary, weight, and at least two concepts. Each concept declares a title, one-line gist, and source ref. A formula or trap is optional but valuable.

`map.html` shows the layer strip, category cards with magnitude, a spoiler tree of big ideas and concepts, the matrix, the route, and the relationship table. Big ideas are visible by default; concepts stay collapsed until opened. The index shows the layer strip and category cards.

The matrix is often the single most useful page for revision. The weights are the study plan: they tell the learner where to spend time and how much practice volume a category has.

## Relationship map

List directional effects. Example format:

| From | To | Mechanism |
|---|---|---|
| Credit | Liquidity | Defaults reduce cash inflow and increase provisioning |
| Market | Liquidity | Collateral values fall and haircuts rise |
| Operations | Reputation | Service outage erodes trust |

## Glossary and abbreviations

- Glossary: terms with a one-sentence definition in plain language.
- Abbreviations: abbreviation, expansion, and context.
- Add search boxes to both.
- Use tooltips for abbreviations in prose, but keep a visible reference table.
- Skip tooltips inside quiz options, links, and the reference table itself.

## Coverage map

Create a source-to-output table. Use the `ref` from `working/normalized.jsonl` when the source is not a slide deck:

| Source | Ref | Content | Output page | Status |
|---|---|---|---|---|
| Slides 1-37 | slide:1-37 | Foundations | foundation.html | covered |
| Slides 38-81 | slide:38-81 | Cluster 1 | topic-01.html | covered |
| handout.docx | paragraph:12 | Shared definition | foundation.html | covered |
| bank.xlsx | Liquidity!row:7 | LCR question | bank-soal.html | covered |
| notes.md | line:20-22 | Exam advice | interview.html | covered |
| Audio session 1 | 00:14:20 | Interview hint | interview.html | covered |

Every slide, page, paragraph, line range, and table row must have a destination or be marked as non-content, such as a cover or thank-you slide. The coverage map is the audit trail. A normalized record that appears nowhere is an omission.

## Naming

Use lowercase hyphenated filenames. Keep navigation labels short. Make the folder readable without a README:

```text
index.html
map.html
foundation.html
topic-01.html ... topic-0N.html
bank-soal.html
interview.html
```

## Writing style

- Lead with purpose, then detail.
- Define a term before using it.
- Prefer concrete examples over abstract descriptions.
- Use "if this, then that" for procedures.
- Keep one idea per paragraph.
- No em dash as a sentence connector.
- Avoid AI filler: "it is important to note", "in today's fast-paced world", "delve into".
