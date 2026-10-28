# Site Build

## Principles

- Static, offline, no CDN, no build step required.
- Light or dark reading surface, white by default, one accent per topic.
- System fonts: sans-serif for headings and UI, serif for long prose, monospace for numbers.
- No dead controls. Every button must work.
- Every page must be readable at 390 px and 1440 px.

## Design tokens

```css
:root {
  --paper: #ffffff;
  --surface: #ffffff;
  --surface-2: #f7f8fa;
  --ink: #121316;
  --ink-2: #34383e;
  --muted: #626a73;
  --faint: #8a919a;
  --line: #e4e7ea;
  --line-strong: #c8ced5;
  --cat: #2f5d4f;
  --cat-soft: #f3f4f6;
  --ok: #2f6b4f;
  --bad: #a02b25;
  --warn: #8a5a1f;
  --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-body: ui-serif, Georgia, "Times New Roman", serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
```

Use category accent colors only for kickers, rules, numbers, dots, and thin borders. Keep cards and callouts white or near-white.

## Dark mode

The starter template uses `data-mode="light"` or `data-mode="dark"` on `<body>`. The dark block overrides surface, ink, line, semantic, accent, tooltip, and topbar tokens. Category themes have lighter dark variants.

A topbar button toggles the mode and stores the choice in `localStorage`. If the brief selects dark, set the body attribute to dark. The toggle still lets the reader switch.

Check contrast for normal text, muted text, callouts, quiz correct and wrong states, the tooltip, and the focus ring. Do not assume that a dark website automatically produces a readable dark video.

## Page shell

- Topbar: brand, section navigation, quiz CTA.
- Sidebar: topic map, progress, mark-as-read button.
- Mobile: menu button and drawer; hide the sidebar.
- Footer: source note, coverage map, abbreviation list.
- Reading progress bar at the top.

## Components

- Callout: 3 px left border, near-white background, uppercase label.
- Process: 4 or 5 equal steps with arrows.
- Table: compact, header background, horizontal scroll wrapper.
- Formula: label and equation rows, monospace for equations.
- Matrix: CSS grid with a colored dot for active cells.
- Trap callout: red border, short bullet list.
- Self-check: `<details>` blocks with answers.

## Quiz

Data schema: see `references/02-question-bank.md`. The quiz should support:

- Four types: single choice, multiple choice, true or false, and short answer.
- At least two options per choice question, with 8 or fewer recommended. Do not hardcode A to D.
- Topic filters and search across questions, options, and accepted answers.
- Shuffle order.
- Check the answer, then show the explanation and trap.
- Multiple choice requires the exact set of correct keys, not a subset.
- Short answer compares normalized text against `accepted_answers`.
- Retry only wrong questions. The retry pool contains only those questions until the filter or search changes.
- List mode for review and print, including accepted answers for short answer.
- Local progress in `localStorage`.
- Keyboard shortcuts for visible option keys and Enter to check or advance.
- No tooltips inside option buttons or the answer input.

Validate the data before opening the page:

```bash
python scripts/quiz_schema.py assets/quiz-data.js
```

Avoid these bugs:

- Do not recompute a shuffled order on every render. Store the order.
- Do not let status counts exceed the active filter.
- Do not attach tooltips to elements that are clicked for selection.
- Do not compare a multiple choice array to a string key.
- Do not auto-check a short answer on every keystroke. Wait for Check.
- Do not lose focus while typing a short answer.

## Print PDF

Create a dedicated print HTML page with all questions, keys, and explanations. Use inline CSS and no navigation.

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="bank-soal/question-bank.pdf" \
  "file:///absolute/path/bank-soal/cetak.html"
```

Verify the PDF page count and question count with PyMuPDF.

## Abbreviations

- Build a dictionary: abbreviation, expansion, context.
- Auto-wrap abbreviations in content text nodes.
- Skip `a`, `button`, `input`, `summary`, `code`, `pre`, `svg`, quiz cards, reference tables, and the glossary.
- Tooltip on hover, keyboard focus, and tap.
- Position fixed, clamp to viewport, hide on scroll and Escape.
- Add a visible abbreviation table for readers who do not hover.

## Accessibility

- Skip link to main content.
- Visible focus states.
- Buttons are real buttons.
- Color is not the only signal.
- Tables have headers.
- Tooltips are supplementary; the same information exists in the abbreviation table.

## Performance

- No external requests.
- Inline SVG for diagrams.
- Lazy-load nothing critical.
- Keep images small and local.
- Test the site with JavaScript disabled for reading pages; navigation and content should still work.
