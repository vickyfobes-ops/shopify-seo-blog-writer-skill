# DOCX V4 Editorial Preview Standard

## Purpose

Use this standard for every English and Chinese Word deliverable. It distills
the approved V4 document structure and visual system without distributing any
reference article copy or image assets.

## Master Lock

This is a single locked editorial master, not a family of optional templates.
Every topic reuses the same page architecture and only swaps the article
content, SEO metadata, factual tables, and image subjects.

Allowed to change by topic:

- title text;
- eyebrow wording within the same buying-guide/planning-guide voice;
- SEO table values;
- article body, formulas, CTA, FAQ, and source links;
- generated image subjects and captions.

Not allowed to change by topic:

- centered cover-page layout;
- design-inspiration or trend-report framing;
- decorative accent colors;
- planned-image cards, image placeholders, or source-only title pages;
- replacing the first-page SEO table with freeform metadata text.

## Page And Safety Labels

- Use US Letter portrait pages with one-inch margins on all sides.
- Repeat a compact 8.5-point header and footer on every page.
- Use `SHOPIFY BLOG DRAFT  |  OFFICE PLANNING GUIDE` for English office topics.
- Use `SHOPIFY BLOG 草稿  |  办公空间规划指南` for Chinese office topics.
- Use the equivalent buying-and-planning label for non-office topics.
- Put `Local preview - not published  |  {PAGE}` in the English footer.
- Put `本地预览 - 未发布  |  {PAGE}` in the Chinese footer.
- Use a real automatic Word page field. Never imply that the article was
  uploaded, drafted, or published in Shopify.

## First Page

Use this order:

1. 9.5-point bold eyebrow.
2. 24-point bold article title.
3. 10-point italic local-preview subtitle.
4. Five-row, two-column SEO metadata table.
5. Embedded hero image.
6. Centered italic image caption.
7. Article opening.

All first-page text remains left aligned except the image caption. Do not use a
centered title page, centered subtitle stack, or oversized cover-page whitespace.

The metadata rows are:

- Field / Value
- Primary keyword
- SEO title
- URL handle
- Search intent

Localize the field labels for the Chinese document while preserving the same
values and table structure.

## Typography

- Body: Calibri 11 point, black, 1.1 line spacing, 6 points after.
- CJK fallback: automatically select an installed sans-serif Chinese font,
  preferring Microsoft YaHei on Windows, Heiti SC on macOS, and Noto Sans CJK
  SC or Source Han Sans SC on Linux.
- Markdown H2 -> Word Heading 1: 16 point bold, 16 points before, 8 after.
- Markdown H3 -> Word Heading 2: 13 point bold, 12 points before, 6 after.
- Markdown H4 -> Word Heading 3: 12 point bold, 8 points before, 4 after.
- Keep headings with the next paragraph.
- Use real Word bullets, numbering, headings, tables, hyperlinks, and fields.
- Keep the presentation neutral and editorial: black text, white pages, thin
  gray rules, and no decorative color theme.
- Text color is locked to `#000000` for body text, headings, metadata, captions,
  header, footer, and hyperlinks. Underlines are allowed for links, but blue,
  gray, automatic, theme-derived, or accent-colored text is not.
- Treat any blue, teal, gold, or brand-accent heading treatment as a failed
  build for this master.

## Tables

- Use fixed-width tables across the 6.5-inch content area.
- Use thin neutral-gray borders and compact cell padding.
- Fill header rows with `F2F2F2` and make them bold.
- In the SEO table, also fill and bold the first column.
- Use 9-point text in the SEO table and 8.5-point text in article tables.
- Prevent rows from splitting across pages and repeat article header rows.

## Images

- Embed every Markdown image after the required original AI asset has been generated and saved locally.
- Use a centered 6.15 x 2.5625-inch frame, matching the preferred 1200:500
  source ratio.
- Preserve descriptive alt text in the Word drawing properties.
- Put a centered 9-point italic caption immediately below each image.
- Do not deliver neutral placeholders. Missing, unsupported, remote-only, or unreviewed images block final Word generation.
- Keep each image with its caption and inspect for distortion after rendering.
- Do not replace embedded images with text cards such as `PLANNED IMAGE 01`,
  filename callouts, or prompt summaries.

## Visual QA

Render both Word files and inspect every page at full resolution. Delivery is
blocked by clipped text, overlapping elements, broken tables, missing glyphs,
distorted images, detached captions, nearly empty spill pages, or a missing
local-preview safety label. It is also blocked when any text uses a color other
than `#000000` or uses a theme-derived text color.

Delivery is also blocked when the document contains magazine-style cover terms
or worksheet labels such as `DESIGN INSPIRATION`, `ENGLISH PUBLISH SOURCE`,
`SHOPIFY SEO EDITORIAL DRAFT`, or `PLANNED IMAGE`.
