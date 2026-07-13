# Output Contract

## Output Location

Use `content/blogs/drafts/` when that project directory exists. Otherwise use `blog-output/<slug>/`.

Create these files:

- `<slug>.md` - English editable source; local revisions may use a `-vN` suffix.
- `<slug>.zh-CN.md` - Chinese review source.
- `<slug>.html` - English Shopify-compatible body preview.
- `<slug>.zh-CN.html` - Chinese preview.
- `<slug>.bilingual.html` - side-by-side or tabbed review page.
- `<slug>.meta.json` - research, SEO, sources, links, image plan, and safety status.
- `<slug>.review.md` - self-review and blockers.

Optional when requested:

- `<slug>.en.docx`
- `<slug>.zh-CN.docx`
- `<slug>-image-preview.jpg`

## Markdown Contract

- Put local workflow notes in an opening HTML comment so they do not enter generated HTML.
- Use exactly one H1.
- Use six to ten H2 sections.
- Keep `## Frequently Asked Questions` or `## 常见问题` as the final H2.
- Use exactly five H3 FAQ questions after the final H2.
- Put at least three external research links in the fifth FAQ answer.
- Include at least five Markdown image placements.
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
  "internalLinkSuggestions": [],
  "imagePlan": [],
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

When a local filename uses `-vN`, keep `seo.urlHandle` canonical without that version suffix. The validator removes a trailing local version automatically, or accepts `--handle <canonical-handle>` explicitly.

## Review Contract

The review must report:

- generated files;
- SEO title and meta-description lengths;
- word, heading, FAQ, image, and source counts;
- originality and factual checks;
- bilingual parity status;
- unverified brand facts or internal URLs;
- publication blockers;
- Shopify API, draft, and publication status.

Do not hide failures behind a score. List them as blockers or warnings.
