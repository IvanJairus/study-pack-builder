# Question Bank

## Goal

Produce one deduplicated question bank where every raw question is accounted for, every answer is validated, and every unique question has a grounded explanation.

## Schema

Use a stable JSON schema. Keep raw source IDs, not only the canonical ID.

```json
{
  "id": "Q01",
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
  "answer": "D",
  "explanation": "Why D is correct and why the main distractors are wrong.",
  "trap": "Short memory hook or exam warning."
}
```

## Extracting highlighted answers

1. Render or parse the PDF with page coordinates.
2. Read vector fills. Use yellow or another key color for the correct option and green or italic notes for explanations.
3. Compute the overlap between every text line and every highlight rectangle.
4. Mark a line highlighted only when a significant part of its area overlaps the fill. This avoids picking up a stem highlight such as "which is NOT".
5. Map highlighted lines to option letters. A question stem may be highlighted; ignore it unless an option is also highlighted.
6. If multiple options are highlighted, flag the question for review.
7. If no option is highlighted, look for a duplicate question with a key. Never guess.

Run:

```bash
python scripts/extract_questions.py answer-key.pdf --out working/questions.json
```

Review the `ambiguous` and `missing_answer` lists before continuing.

## Parsing rules

- A question starts with a number at the beginning of a line. Ignore years and numbered content inside options.
- Options start with `A.`, `B.`, `C.`, `D.` or an OCR-recognized bullet plus letter.
- Concatenate wrapped lines into the last option until a new option or question starts.
- Preserve section headers because they help with topic classification.
- Fix obvious OCR/typos only when the meaning is unambiguous.
- Keep a note when the source itself is truncated or contradictory.

## Cross-checking

Use every available source:

- Answer-key PDFs.
- Online forms or exported score pages.
- Screenshots of question forms.
- Duplicate questions across sets.

For forms, compare option content, not letter order. Forms often shuffle options. Use the form's green correct-answer highlight as a second opinion, not as an override without inspection.

## Deduplication

1. Normalize text: lowercase, remove punctuation, collapse whitespace, drop common stopwords.
2. Compute similarity between question stems. Use `difflib.SequenceMatcher` for short sets or embeddings for large sets.
3. Cluster at a threshold that catches rephrasing but not different asks. Inspect every merged cluster.
4. Split clusters that combine different questions, for example "purpose of measurement" versus "purpose of monitoring".
5. Choose the most complete wording as canonical. Keep all raw variants as source IDs.
6. Ensure every raw question appears exactly once across all clusters.

```bash
python scripts/dedup_questions.py working/questions.json --out working/clusters.json
```

## Answer integrity

Validate:

- Answer is one of the option letters.
- Exactly four options per question.
- No empty option.
- Explanation and trap are non-empty.
- Source count matches the number of distinct sets.
- All raw source IDs are represented exactly once.

## Explanations

Each explanation should:

1. State why the key is correct.
2. Explain the strongest distractor.
3. Name the exam trap in one short sentence.
4. Reference the source slide range when available.
5. Mark uncertainty when the source is inconsistent.

Do not write generic filler. If the material does not support an explanation, flag the question instead of inventing one.

## Frequency

Frequency is useful for prioritization, but it is not a substitute for coverage. A question that appears once can still be the only question on an important topic.
