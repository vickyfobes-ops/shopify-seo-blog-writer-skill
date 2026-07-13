# Shopify SEO Blog Writer Skill for Codex

Turn one topic into a complete, bilingual Shopify SEO blog bundle.

This open-source Codex Skill researches current search intent, writes an English Shopify blog and Chinese review copy, creates SEO metadata and HTML, plans images, adds source links at the end, and validates the local bundle. It is designed for product education, buying guides, comparison posts, problem-solving articles, and custom-product planning content.

## What It Produces

- English SEO blog source
- Chinese review translation
- English, Chinese, and bilingual HTML previews
- SEO title, meta description, URL handle, tags, and excerpt
- Research notes and source links
- Five-question FAQ with sources at the end
- At least five image placements with alt text and prompts
- Editorial review and publication blockers

Shopify API calls and publishing are disabled by default.

## Install

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

## License

MIT
