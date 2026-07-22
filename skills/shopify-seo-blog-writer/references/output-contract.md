# Output Contract

## Output Location

Use `content/blogs/drafts/` when that project directory exists. Otherwise use `blog-output/<slug>/`.

Create these files:

- `<slug>.en.docx` - primary English Word deliverable.
- `<slug>.zh-CN.docx` - primary Chinese Word deliverable.
- `<slug>.md` - English editable source; local revisions may use a `-vN` suffix.
- `<slug>.zh-CN.md` - Chinese review source.
- `<slug>.html` - English Shopify-compatible body preview.
- `<slug>.zh-CN.html` - Chinese preview.
- `<slug>.bilingual.html` - side-by-side or tabbed review page.
- `<slug>.meta.json` - research, SEO, sources, links, image plan, and safety status.
- `<slug>.review.md` - self-review and blockers.
- `images/<slug>/` - at least five finished original AI design renders used by both languages; prefer seven for long guides.

Optional when requested:

- `<slug>-image-preview.jpg`

## DOCX Contract

- Treat both Word files as required, user-facing deliverables. Never omit them silently.
- Build each DOCX from its matching Markdown source after factual and bilingual review.
- Preserve the complete heading order, prose, numbers, units, tables, lists, CTA, FAQ, links, and source notes.
- Apply `docx-format-standard.md`: US Letter portrait, exact one-inch margins, V4 first-page front matter, neutral black-and-white typography, Calibri 10.5-point (五号) body text, and no page headers or footers.
- Embed every Markdown image in a centered 6.15 x 2.5625-inch frame with alt text and a caption.
- Missing, remote-only, unsupported, or placeholder images block final DOCX generation. The optional `--allow-placeholders` generator flag is for debugging only and does not satisfy bundle validation.
- Use real Word heading styles, real lists, readable fixed-width tables, and clickable links. Do not create header/footer parts or page fields.
- Keep the approved buying-guide master locked. The final DOCX must not become a
  centered cover-page template, a design-inspiration deck, a planned-image
  worksheet, or a source-only editorial wrapper.
- Render and inspect every page when a DOCX renderer is available. Record the result in the review report.
- If visual rendering is unavailable, run structural DOCX validation and report that visual QA was unavailable; the DOCX files are still mandatory.

## Markdown Contract

- Put local workflow notes in an opening HTML comment so they do not enter generated HTML.
- Use exactly one H1.
- Use six to ten H2 sections.
- Keep `## Frequently Asked Questions` or `## 常见问题` as the final H2.
- Use exactly five H3 FAQ questions after the final H2.
- Put at least three external research links in the fifth FAQ answer.
- Include at least five distinct local Markdown image placements, each backed by a finished 1200 x 500 PNG or JPEG. English and Chinese must use the same assets in the same order.
- Put the CTA immediately before FAQ.

## Metadata Contract

Use valid UTF-8 JSON. Include at least:

```json
{
  "version": "v1",
  "generatedAt": "YYYY-MM-DD",
  "topic": "User topic",
  "keyword": "primary keyword",
  "searchIntent": "commercial investigation",
  "editorialStrategy": {
    "structureFamily": "case-process-analysis | diagnostic-troubleshooting | decision-comparison | sizing-planning | material-finish | delivery-installation | care-maintenance",
    "selectedStructure": "Topic-specific section progression",
    "openingMode": "verdict-first | constraint-first | diagnostic-observation | comparison-tension | misconception-correction | process-stakes",
    "openingSignature": "Normalized first 12 words",
    "recentStructureSimilarityCheck": "passed",
    "recentOpeningSimilarityCheck": "passed"
  },
  "contentMetrics": {
    "englishBodyWords": 0,
    "h1Count": 1,
    "h2Count": 0,
    "faqCount": 5,
    "imageCount": 0
  },
  "researchSummary": {
    "secondaryKeywords": [],
    "userQuestions": [],
    "competitorPatterns": [],
    "contentGapsAddressed": []
  },
  "researchSources": [
    {
      "title": "Source title",
      "url": "https://example.com/source",
      "usedFor": "Claim or planning concept supported"
    }
  ],
  "seo": {
    "seoTitle": "45 to 60 characters",
    "seoTitleLength": 0,
    "metaDescription": "140 to 160 characters",
    "metaDescriptionLength": 0,
    "urlHandle": "lowercase-hyphenated-slug",
    "excerpt": "Short summary",
    "shopifyTags": []
  },
  "ctaStrategy": {
    "primaryCtaTrigger": "design-case | troubleshooting | size-planning | material-approval | buying-comparison | delivery-installation | care-maintenance | brand-trust",
    "ctaPresentation": "integrated-conclusion | split-action-block | expertise-bridge | summary-brand-bridge | evidence-or-brief-request",
    "ctaPattern": "The intent-specific closing function selected from the CTA matrix",
    "requestedInputs": [],
    "destination": {
      "label": "Real page or collection name, or empty",
      "url": "Verified internal URL, or empty"
    },
    "brandProofUsed": [],
    "brandProofReason": "Why a verified metric is necessary, or empty when no metric is used",
    "recentDraftSimilarityCheck": "passed"
  },
  "internalLinkSuggestions": [],
  "imageGeneration": {
    "required": true,
    "sourceType": "ai-generated-original",
    "generatedCount": 5,
    "disclosure": "Original AI design visualizations; not customer-project photography."
  },
  "visualBrief": {
    "topic": "Current article topic",
    "audience": "Reader and buying stage",
    "visualStyle": "Topic-appropriate visual direction",
    "sectionRationale": "Why each visual role supports this topic's decisions"
  },
  "imagePlan": [
    {
      "imagePurpose": "What this image helps the reader inspect",
      "imagePrompt": "Full generation prompt",
      "fileName": "descriptive-image-name.png",
      "localPath": "images/<slug>/descriptive-image-name.png",
      "altText": "Specific descriptive alt text",
      "insertAfterHeading": "H1 or section heading",
      "imageRatio": "1200:500",
      "sourceType": "ai-generated-original",
      "status": "generated"
    }
  ],
  "selfReview": {
    "aiToneScore": 0,
    "originalityRiskScore": 0,
    "seoScore": 0,
    "seoScoreType": "Internal on-page readiness score, not a ranking guarantee",
    "conversionScore": 0,
    "factualRisk": 0,
    "riskWarnings": []
  },
  "publicationBlockers": [],
  "shopify": {
    "apiCalled": false,
    "draftCreated": false,
    "published": false
  }
}
```

The validator accepts extra fields. Keep source support, unverified URLs, assumptions, and blockers explicit.

`editorialStrategy` and `ctaStrategy` are required quality records, not decorative metadata. Select them before drafting and update them if the finished article changes. A similarity check may be `not-available` only when no recent local drafts exist; explain that limitation in the review.

When a local filename uses `-vN`, keep `seo.urlHandle` canonical without that version suffix. The validator removes a trailing local version automatically, or accepts `--handle <canonical-handle>` explicitly.

## Review Contract

The review must report:

- generated files;
- English and Chinese DOCX generation and visual-QA status;
- original AI image count, local paths, generation status, visual-QA status, and disclosure;
- SEO title and meta-description lengths;
- word, heading, FAQ, image, and source counts;
- originality and factual checks;
- selected structure family, opening mode, opening-similarity check, structure-similarity check, CTA trigger, and CTA presentation;
- bilingual parity status;
- unverified brand facts or internal URLs;
- publication blockers;
- Shopify API, draft, and publication status.

Do not hide failures behind a score. List them as blockers or warnings.
