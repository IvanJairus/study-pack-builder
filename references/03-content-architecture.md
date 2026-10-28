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

Use a consistent order:

1. Kicker and title.
2. One-sentence orientation.
3. "30-second essentials", three to five bullets.
4. The process sequence as a visual.
5. Definition and scope.
6. Factors or parameters in a table.
7. Measurement methods and formulas.
8. Monitoring and controls.
9. Reporting frequency and recipients.
10. Exam traps.
11. Self-check questions.
12. Source ranges and related pages.

This order reduces memory load: the learner sees the big picture before the details.

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

## Topic map

Create one visual and one matrix:

- Visual: center = the shared framework, surrounding nodes = clusters.
- Matrix: rows = clusters, columns = process steps, cells = key artifacts.

The matrix is often the single most useful page for revision.

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
