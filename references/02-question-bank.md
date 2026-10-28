# Question Bank

## Goal

Produce one deduplicated question bank where every raw question is accounted for, every answer is validated, and every unique question has a grounded explanation. The bank supports single choice, multiple choice, true or false, and short answer questions with a variable number of options.

## Schema

Use a stable JSON schema. Keep raw source IDs, not only the canonical ID.

```json
{
  "id": "Q01",
  "type": "single_choice",
  "source_ids": ["S1-03", "S2-22", "S3-20"],
  "frequency": 3,
  "topic": "Liquidity",
  "slides": "Slides 126-161",
  "question": "What is the purpose of liquidity risk measurement?",
  "options": {
    "A": "Option A text",
    "B": "Option B text",
    "C": "Option C text",
    "D": "Option D text"
  },
  "order": ["A", "B", "C", "D"],
  "answer": "D",
  "explanation": "Why D is correct and why the main distractors are wrong.",
  "trap": "Short memory hook or exam warning."
}
```

## Question types

| Type | Options | Answer | Use |
|---|---|---|---|
| `single_choice` | 2 or more keys, uppercase letters | one key | Default when type is omitted |
| `multiple_choice` | 2 or more keys, uppercase letters | array of at least 2 keys | Select all that apply |
| `true_false` | omit options | boolean `true` or `false` | Two statements, no custom options |
| `short_answer` | omit options | `accepted_answers` array | Typed answer with accepted variants |

Rules:

- `topic` is required. It drives the quiz filter.
- `order` is optional. When present, list every option key exactly once.
- `question`, `explanation`, and `trap` are required for every type.
- For `short_answer`, include `accepted_answers` with spelling variants, abbreviations, and both languages when the source uses both.
- A missing `type` is treated as `single_choice` so older banks still validate. Add the type explicitly for new banks.
- `source_count` should match the length of `sources` when both are present.
- Option texts should be distinct. Duplicate option text produces a warning.

## Extracting highlighted answers

1. Render or parse the PDF with page coordinates.
2. Read vector fills. Use yellow or another key color for the correct option and green or italic notes for explanations.
3. Compute the overlap between every text line and every highlight rectangle.
4. Mark a line highlighted only when a significant part of its area overlaps the fill. This avoids picking up a stem highlight such as "which is NOT".
5. Map highlighted lines to option letters. A question stem may be highlighted; ignore it unless an option is also highlighted.
6. If multiple options are highlighted, set `type` to `multiple_choice` and `answer` to the array of keys. Do not guess a single answer.
7. If no option is highlighted, look for a duplicate question with a key. Never guess.

Run:

```bash
python scripts/extract_questions.py answer-key.pdf --out working/questions.json
```

Review the `ambiguous` and `missing_answer` lists before continuing.

## Parsing rules

- A question starts with a number at the beginning of a line. Ignore years and numbered content inside options.
- Options start with `A.` through `H.` or an OCR-recognized bullet plus letter.
- Concatenate wrapped lines into the last option until a new option or question starts.
- Preserve section headers because they help with topic classification.
- Fix obvious OCR or typos only when the meaning is unambiguous.
- Keep a note when the source itself is truncated or contradictory.

## Cross-checking

Use every available source:

- Answer-key PDFs.
- Online forms or exported score pages.
- Screenshots of question forms.
- Duplicate questions across sets.
- CSV or XLSX question exports.

For forms, compare option content, not letter order. Forms often shuffle options. Use the form's green correct-answer highlight as a second opinion, not as an override without inspection.

## Deduplication

1. Normalize text: lowercase, remove punctuation, collapse whitespace, drop common stopwords.
2. Compute similarity between question stems. Use `difflib.SequenceMatcher` for short sets or embeddings for large sets.
3. Only cluster questions with the same type. A single choice question and a multiple choice question are different asks.
4. Cluster at a threshold that catches rephrasing but not different asks. Inspect every merged cluster.
5. Split clusters that combine different questions, for example "purpose of measurement" versus "purpose of monitoring".
6. Choose the most complete wording as canonical. Keep all raw variants as source IDs.
7. Ensure every raw question appears exactly once across all clusters.
8. Review `answer_conflict: true` in the cluster output. It means members disagree on the key.

```bash
python scripts/dedup_questions.py working/questions.json --out working/clusters.json
```

## Answer integrity

Validate:

- Answer is one of the option letters for single choice.
- Multiple choice answer is an array of at least two valid keys.
- True or false answer is a boolean.
- Short answer has at least one accepted variant.
- Every choice question has at least 2 non-empty options; 8 or fewer reads better.
- Explanation and trap are non-empty.
- Source count matches the number of distinct sets.
- All raw source IDs are represented exactly once.

Run the validator on the final data file:

```bash
python scripts/quiz_schema.py assets/js/quiz-data.js
python scripts/quiz_schema.py working/questions.json --strict
```

`check_site.py --quiz` uses the same validator, so a passing schema check and a passing site check agree.

## Explanations

Each explanation should:

1. State why the key is correct.
2. Explain the strongest distractor.
3. For multiple choice, explain every correct key and the most tempting wrong option.
4. For short answer, explain what the accepted variants have in common.
5. Name the exam trap in one short sentence.
6. Reference the source slide, page, or normalized ref when available.
7. Mark uncertainty when the source is inconsistent.

Do not write generic filler. If the material does not support an explanation, flag the question instead of inventing one.

## Frequency

Frequency is useful for prioritization, but it is not a substitute for coverage. A question that appears once can still be the only question on an important topic.
