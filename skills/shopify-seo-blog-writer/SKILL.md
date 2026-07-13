---
name: shopify-seo-blog-writer
description: Turn one product or content topic into a complete, bilingual, source-backed Shopify SEO blog bundle. Use when Codex needs to research search intent, select keywords, write an English publish-ready article and Chinese review copy, produce SEO metadata and HTML, plan images, add end-of-article sources, or audit a Shopify blog draft. Default to local files only; never call Shopify, create a Shopify draft, or publish unless the user explicitly requests that separate action.
---

# Shopify SEO Blog Writer

## Objective

Convert a topic into a useful buying or planning article, not a keyword-expanded essay. Work from the room, product, use case, constraints, and buyer decision whenever the topic allows it.

Accept a topic as the only required input. Infer reasonable defaults and continue without asking questions unless a missing fact would make the article unsafe or materially false.

## Load References

Read these files before drafting:

- `references/quality-standard.md` for the V5-derived editorial benchmark.
- `references/research-and-seo.md` for keyword, intent, source, and originality rules.
- `references/output-contract.md` for filenames, metadata, and validation requirements.

Also read project-level `AGENTS.md`, brand guides, product facts, and approved examples when present. Treat historical blogs as style references only; never copy their wording.

## Default Deliverable

Create all of the following from one topic:

1. English SEO blog source.
2. Chinese review translation that mirrors the English meaning.
3. English and Chinese HTML.
4. Bilingual HTML review page.
5. SEO metadata JSON with research, scores, sources, internal-link suggestions, and image plan.
6. Review report with factual, SEO, originality, and publication checks.

Use the existing `content/blogs/drafts/` directory when available. Otherwise create `blog-output/<slug>/`. Follow the exact names in `references/output-contract.md`.

## Workflow

### 1. Resolve the Brief

- Use the supplied topic as the main subject.
- Infer the likely audience, funnel stage, search intent, and primary market.
- Use English as the publish language and Chinese as the review language unless the user specifies otherwise.
- Use inches throughout when the market is the United States or is unspecified. Use one unit system consistently for other markets.
- Discover brand and product facts from local project files. If none exist, write brand-neutral copy and mark CTA or internal URL placeholders as unverified.
- Never invent experience, customer counts, projects, prices, lead times, certifications, warranties, test results, or performance claims.

### 2. Research Before Writing

- Browse current search results when web access is available.
- Identify the primary keyword, 4-8 secondary keywords, search intent, common questions, competitor patterns, and content gaps.
- Prefer primary sources: official standards, regulators, original manufacturers, technical documentation, and first-party product information.
- Use at least three credible sources when the article contains dimensions, safety guidance, standards, performance claims, or other factual ranges.
- Record what each source supports. Do not use a source merely because it ranks.
- If web access is unavailable, avoid unstable claims and mark source verification as incomplete in the review.

### 3. Build the Decision Structure

- Open with a direct answer in the first 120 words.
- Select one recommended default when readers face competing values.
- Label alternatives as verified compact options, occasional maximums, or project-specific exceptions.
- State formulas and worked examples when they reduce ambiguity.
- Explain why the recommendation changes when room size, fixed furniture, product dimensions, access, power, installation, or regulations change.
- Plan 6-10 H2 sections. Keep the final H2 as FAQ with exactly five high-intent questions.
- Make the fifth FAQ question a source note and place all research links in its answer. Add nothing after FAQ.

### 4. Draft the English Article

- Target 1,800-2,600 words unless the search intent clearly needs less.
- Use one H1 containing the primary keyword naturally.
- Put the primary keyword in the opening, one useful H2, the conclusion, and metadata without forcing repetition.
- Use tables only when they help compare concrete choices.
- Include a practical CTA before FAQ. Use only verified URLs; otherwise label local suggestions as unverified in metadata.
- Keep claims qualified as planning guidance when they are not legal or engineering requirements.

### 5. Produce the Chinese Review Copy

- Mirror every heading, fact, number, qualification, link, CTA, FAQ, and source.
- Translate for natural Chinese review, not word-for-word stiffness.
- Preserve the same unit system and decision hierarchy.
- Do not add claims that are absent from the English source.

### 6. Plan Images

- Plan at least five images; prefer seven for a long guide.
- Include purpose, insertion point, filename, alt text, aspect ratio, and generation or photography prompt.
- Use descriptive, topic-specific alt text. Do not stuff the main keyword into every image.
- Do not claim generated images show completed customer projects.

### 7. Create Metadata and Review

- Keep the SEO title between 45 and 60 characters.
- Keep the meta description between 140 and 160 characters.
- Use a lowercase hyphenated canonical handle without local version suffixes.
- Distinguish internal on-page readiness scores from ranking guarantees.
- Record all source URLs, factual guardrails, unverified internal links, and publication blockers.
- Set `apiCalled`, `draftCreated`, and `published` to `false` by default.

### 8. Validate and Revise

Run:

```bash
python <skill-dir>/scripts/validate_bundle.py --dir <output-directory> --slug <slug>
```

Fix every error before handing off. Review warnings and either fix them or explain them in the review report.

If Word files are requested and a document-generation tool is available, generate English and Chinese `.docx`, render every page, and inspect for clipping, broken tables, missing glyphs, image distortion, bad page breaks, and nearly empty spill pages.

## Safety Boundary

- Produce local drafts only by default.
- Do not call Shopify Admin APIs, create drafts, upload images, or publish.
- Do not modify existing live content.
- Perform any Shopify action only after a separate, explicit user instruction and preserve `published: false` unless publication is explicitly requested.
