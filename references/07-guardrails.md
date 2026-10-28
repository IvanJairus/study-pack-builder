# Guardrails

## Privacy

- Never commit source PDFs, PPTX files, audio, screenshots, or extracted transcripts to a public repository.
- Keep `working/normalized.jsonl` and its summary out of the final deliverable and the public repository. They contain source text and paths.
- `sumber/source-inventory.json` and `sumber/coverage-map.md` are metadata and may ship with the local pack. Use relative paths and review hashes before publishing.
- Do not execute macros from XLSM, DOCM, or other Office files. The normalizer reads document XML only.
- Remove names, employee IDs, unit names, email addresses, phone numbers, and organization logos from public examples.
- Use synthetic examples for tests and documentation.
- Add a `.gitignore` before the first commit, not after.
- Check staged files with `git status` and inspect anything that looks like a source document.

## Copyright

- Summarize and paraphrase. Do not reproduce long passages.
- Short quotes are acceptable when they are necessary for explanation and carry attribution.
- Do not redistribute paid course material, exam questions, or proprietary slides.
- If the source license is unclear, keep the output private and ask the user.
- Preserve license notices when using third-party assets or code.

## Accuracy

- The official source wins over audio, memory, or inference.
- If two sources conflict, show both and mark the conflict.
- If a key is missing, mark it unresolved. Do not fill it by guessing.
- Distinguish "source says" from "my interpretation".
- Do not invent citations, page numbers, or timestamps.

## Exam integrity

- Build study aids, practice questions, and explanations.
- Do not help someone bypass an exam, impersonate a candidate, or leak live exam content.
- Do not claim that a practice answer is guaranteed to appear.

## Distribution

- Public repos must contain only code, templates, synthetic examples, and documentation.
- Before pushing, run a scan for private names, domains, IDs, and source filenames.
- Use MIT or another explicit license if the user wants reuse.
- Add a short disclosure when audio or video is machine-generated.

## AI disclosure

- Transcripts are machine-generated and may contain errors.
- TTS narration is synthetic.
- Summaries are study aids, not official documents.
- State the source of truth in the footer of the website and in the video description.

## Quality

- A visually polished page can still be wrong. Check facts, counts, and links.
- A green build can still be unusable. Open it, click it, and read it.
- A high question count is not a quality signal. Coverage, correctness, and explanation quality matter more.
