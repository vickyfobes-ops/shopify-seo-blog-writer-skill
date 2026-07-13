# Shopify SEO Blog Writer Skill for Codex

Turn one topic into a complete, bilingual Shopify SEO blog bundle delivered in Word.

This open-source Codex Skill researches current search intent, writes an English Shopify blog and Chinese review copy, creates polished English and Chinese DOCX files, produces SEO metadata and HTML, plans images, adds source links at the end, and validates the local bundle. It is designed for product education, buying guides, comparison posts, problem-solving articles, and custom-product planning content.

## What It Produces

- English DOCX publication-review document in the approved V4 editorial format
- Chinese DOCX review document with the same layout and reliable CJK fonts
- English SEO blog source and Chinese review translation
- English, Chinese, and bilingual HTML previews
- SEO title, meta description, URL handle, tags, and excerpt
- Research notes and source links
- Five-question FAQ with sources at the end
- At least five image placements with alt text and prompts
- Editorial review and publication blockers

Shopify API calls and publishing are disabled by default.

## Install

Python 3.10 or newer is required for the bundled generator and validator.

Use the Codex skill installer:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo vickyfobes-ops/shopify-seo-blog-writer-skill \
  --path skills/shopify-seo-blog-writer
```

Or install manually:

```bash
git clone https://github.com/vickyfobes-ops/shopify-seo-blog-writer-skill.git
cp -R shopify-seo-blog-writer-skill/skills/shopify-seo-blog-writer ~/.codex/skills/
```

The Skill is available to Codex on the next turn after installation.

## Use

Topic-only prompt:

```text
Use $shopify-seo-blog-writer for: epoxy conference table size guide
```

Chinese prompt:

```text
使用 $shopify-seo-blog-writer，选题：环氧树脂厨房岛台常见问题
```

Optional context can include a brand guide, product facts, market, audience, target word count, or preferred CTA. None is required to start.

The two primary files are always:

```text
<slug>.en.docx
<slug>.zh-CN.docx
```

No extra “export Word” request is needed. The Skill also retains Markdown, HTML, JSON, and review files as supporting material.

Both Word files use the same approved review format: a local-draft header and
footer, first-page SEO information table, real embedded 1200:500 images,
black-and-white editorial typography, readable comparison tables, and automatic
page numbers. They are labeled as local previews and are not published to
Shopify.

## Quality Standard

The Skill uses a decision-first editorial standard:

- answer the main query near the top;
- choose one recommended default instead of presenting conflicting values equally;
- separate daily recommendations from compact or occasional maximums;
- use one unit system consistently;
- verify measurable claims with credible sources;
- keep FAQ as the final section and put sources in the fifth answer;
- never invent brand facts, customer stories, certifications, or performance promises.

## Validate an Output Bundle

```bash
python skills/shopify-seo-blog-writer/scripts/validate_bundle.py \
  --dir path/to/output \
  --slug your-blog-slug
```

The validator uses only the Python standard library.

The bundled DOCX generator also uses only the Python standard library. It
creates the approved V4 Word layout with real headings, lists, fixed-width
tables, clickable links, embedded images, localized headers and footers, and
automatic page numbering. The validator checks these format requirements in
addition to content completeness.

## License

MIT
