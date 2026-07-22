---
name: shopify-seo-blog-writer
description: Turn one product or content topic into a complete, bilingual, source-backed Shopify SEO blog bundle with original AI design renders embedded in English and Chinese DOCX. Use when Codex needs to research search intent, select keywords, write an English publish-ready article and Chinese review copy, generate topic-specific original images, create polished Word documents, produce SEO metadata and HTML, add end-of-article sources, or audit a Shopify blog draft. Default to local files only; never call Shopify, create a Shopify draft, upload images, or publish unless the user explicitly requests that separate action.
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
- `references/docx-format-standard.md` for the approved V4 Word layout and visual-QA rules.
- `references/ai-image-workflow.md` for mandatory original-image generation, disclosure, and asset checks.

Also read project-level `AGENTS.md`, brand guides, product facts, and approved examples when present. Treat historical blogs as style references only; never copy their wording.

## Locked DOCX Master

Use exactly one Word visual system: the approved V4 commercial buying-guide
editorial preview. Future topics may change the keyword, title, body copy,
tables, formulas, images, and CTA, but they must not switch the document into a
magazine cover, inspiration board, centered title page, trend report, or
template-style showcase.

Locked elements:

- left-aligned first-page stack;
- compact guide eyebrow;
- large left-aligned title;
- italic local-preview subtitle;
- five-row SEO table on page one;
- embedded hero image on page one;
- black text only;
- no page header or footer;
- real embedded images instead of planned-image cards or text placeholders.

Variable elements:

- topic, keyword, H2 structure, formulas, FAQs, image subjects, and localized
  labels;
- body text in Calibri 10.5 point (五号) with no fixed brand identity;
- factual content, visual brief, and image prompts for the current topic only.

## Default Deliverable

Create all of the following from one topic:

1. English Word document as the primary publication-review deliverable.
2. Chinese Word document that mirrors the English meaning.
3. English SEO blog source and Chinese review source.
4. English and Chinese HTML.
5. Bilingual HTML review page.
6. At least five original AI design renders saved as local 1200 x 500 image assets; prefer seven for long guides.
7. SEO metadata JSON with research, scores, sources, internal-link suggestions, and image-generation provenance.
8. Review report with factual, SEO, originality, image, DOCX, and publication checks.

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

- Choose one intent-matched structure family and one opening mode from `references/quality-standard.md` before drafting. Record both in metadata.
- Compare the planned H2 sequence, opening signature, and CTA combination with the current batch and recent local drafts. Change at least two of those three dimensions when similarity is high.
- Open with a useful answer or diagnostic orientation in the first 120 words without forcing every article into the same verdict-first sentence pattern.
- Select one recommended default when readers face competing values.
- Label alternatives as verified compact options, occasional maximums, or project-specific exceptions.
- State formulas and worked examples when they reduce ambiguity.
- Explain why the recommendation changes when room size, fixed furniture, product dimensions, access, power, installation, or regulations change.
- Plan 6-10 H2 sections. Keep the final H2 as FAQ with exactly five high-intent questions.
- Make the fifth FAQ question a source note and place all research links in its answer. Add nothing after FAQ.

### 4. Draft the English Article

- Target 1,800-2,600 words unless the search intent clearly needs less.
- Use one H1 containing the primary keyword naturally.
- Do not begin with “If you want the short answer,” “The short answer is,” or a lightly paraphrased reusable opener. Make the first sentence topic-specific and consistent with the selected opening mode.
- Put the primary keyword in the opening, one useful H2, the conclusion, and metadata without forcing repetition.
- Use tables only when they help compare concrete choices.
- Include a practical CTA before FAQ. Use only verified URLs; otherwise label local suggestions as unverified in metadata.
- Keep claims qualified as planning guidance when they are not legal or engineering requirements.

### 5. Produce the Chinese Review Copy

- Mirror every heading, fact, number, qualification, link, CTA, FAQ, and source.
- Translate for natural Chinese review, not word-for-word stiffness.
- Preserve the same unit system and decision hierarchy.
- Do not add claims that are absent from the English source.

### 6. Generate and Embed Original AI Images

- Follow `references/ai-image-workflow.md`; an image plan alone is not a deliverable.
- Use the mandatory prompt shell in that reference once per image; replace every variable from the current article's visual brief. Call the available image-generation tool once for each selected asset before building either DOCX.
- Derive a new visual brief from the current topic, keyword, search intent, product facts, and article sections. Do not reuse a fixed image set, generic prompt set, or another topic's filenames.
- Generate at least five distinct images and prefer seven for a long guide. Use the built-in image-generation capability when available, with one focused prompt per asset.
- Save every selected result inside `<output-directory>/images/<slug>/` and normalize it to exactly 1200 x 500 pixels without stretching. Never leave a referenced asset only in a temporary or model-output directory.
- Insert the same local image files in the same order in English Markdown, Chinese Markdown, English HTML, and Chinese HTML. Localize the alt text without changing its factual meaning.
- Record purpose, insertion point, filename, local path, alt text, 1200:500 ratio, full prompt, `sourceType: ai-generated-original`, and `status: generated` in metadata.
- Inspect every image for malformed products, text artifacts, logos, watermarks, impossible geometry, misleading measurements, and visual duplication.
- Label the assets as original AI design visualizations. Never describe them as completed products, customer projects, engineering drawings, accessibility certifications, or proof of real-world performance.
- Do not substitute neutral placeholders. If image generation is unavailable or any required asset fails review, report a blocker and do not present the DOCX bundle as complete.

### 7. Create Metadata and Review

- Keep the SEO title between 45 and 60 characters.
- Keep the meta description between 140 and 160 characters.
- Use a lowercase hyphenated canonical handle without local version suffixes.
- Distinguish internal on-page readiness scores from ranking guarantees.
- Record all source URLs, factual guardrails, unverified internal links, and publication blockers.
- Set `apiCalled`, `draftCreated`, and `published` to `false` by default.

### 8. Validate and Revise

Build both required Word documents only after the Markdown sources and all local images are final:

```bash
python <skill-dir>/scripts/build_docx.py --input <output-directory>/<slug>.md --meta <output-directory>/<slug>.meta.json --output <output-directory>/<slug>.en.docx --language en-US
python <skill-dir>/scripts/build_docx.py --input <output-directory>/<slug>.zh-CN.md --meta <output-directory>/<slug>.meta.json --output <output-directory>/<slug>.zh-CN.docx --language zh-CN
```

Treat DOCX as the primary result shown to the user. Follow the V4 format reference exactly: no page header or footer, Calibri 10.5-point (五号) body text, first-page SEO table, real embedded 1200:500 original AI images, `#000000` text for every text role (including hyperlinks), and one-inch Letter-page margins. Use only the brand information supplied for the current task; otherwise keep the article, CTA, and document metadata brand-neutral. The generator fails on missing or unsupported images by default; `--allow-placeholders` is for debugging only and can never satisfy final bundle validation. Keep Markdown, HTML, JSON, review files, and generated image assets as supporting deliverables for editing and automation.

Use `scripts/build_docx.py` as the required document generator for final
deliverables. Do not replace it with an ad hoc DOCX writer, a generic report
template, a centered cover-page template, or another style system. If the final
Word file resembles a design-inspiration deck, planned-image worksheet, or
source-only cover page, treat that as a failed build and rebuild it in the V4
master.

When a document-generation and rendering tool is available, use it to render every DOCX page and inspect for clipping, broken tables, missing glyphs, image distortion, bad page breaks, and nearly empty spill pages. Revise and rerender until clean. When rendering is unavailable, use the bundled generator and structural validator, then state that visual QA was unavailable in the review report. Never skip either DOCX.

Run:

```bash
python <skill-dir>/scripts/validate_bundle.py --dir <output-directory> --slug <slug>
```

Fix every error before handing off. Review warnings and either fix them or explain them in the review report.

## Safety Boundary

- Produce local drafts only by default.
- Do not call Shopify Admin APIs, create drafts, upload images, or publish.
- Do not modify existing live content.
- Perform any Shopify action only after a separate, explicit user instruction and preserve `published: false` unless publication is explicitly requested.
