# Expected Output

A correct run on this synthetic example should produce:

- A study site with a foundation page and a reliability topic page.
- A question bank with 5 raw questions and 3 unique clusters:
  - S1-01 and S2-01 merge into one SLO question.
  - S1-02 and S3-01 merge into one MTTR question.
  - S1-03 remains a single error-budget question.
- Every raw question ID appears exactly once in the cluster output.
- Each unique question has a valid answer for its type, an explanation, and a trap.
- `questions-flexible.json` validates with single choice, multiple choice, true or false, and short answer examples, including a five-option multiple choice and a three-option single choice.
- A coverage map that links the synthetic source sections to the site pages.
- `normalize_source.py` turns text sources into JSONL with line or paragraph refs, and spreadsheet rows keep their physical row numbers.
