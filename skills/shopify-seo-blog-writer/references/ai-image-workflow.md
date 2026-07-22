# Original AI Image Workflow

## Delivery Rule

Generate finished image assets, not prompts alone. Every completed bundle needs at least five distinct original AI design visualizations; use seven for a long buying or planning guide. The English and Chinese documents share the same assets.

Use the available image-generation skill or built-in image-generation tool. Generate one asset per focused prompt. Do not replace image generation with SVG, CSS, stock search, a neutral placeholder, or a text-only image plan.

If image generation is unavailable, record a blocker and stop before final DOCX delivery. Do not claim that a placeholder-based document is complete.

## Topic-First Visual Brief

Do not reuse a fixed conference-table image set, generic prompts, or filenames for a new topic. Before generating, derive a fresh visual brief from the supplied topic, keyword, article angle, intended buyer, product facts, and planned H2 sections.

Choose visual roles that match the search intent:

- Product or buying guide: product hero, scale and room context, key material detail, real-use configuration, comparison, delivery or installation, CTA-aligned closing scene.
- Planning or dimensions guide: room-fit context, seating or circulation view, usable-surface detail, relevant power or access context, base/support or delivery scene.
- Material or finish guide: material hero, close-up construction detail, finish comparison, care/use context, compatible room or product configuration.
- How-to or process guide: credible stage-by-stage product or workshop scenes, tools or materials when relevant, final-use result. Do not fabricate safety certifications or results.
- Problem-solving guide: visualized symptom or constraint, relevant material or setup detail, corrected configuration, and maintenance or prevention context. Never create deceptive before-and-after claims.

Every prompt must visibly connect to the section it supports. Vary the material, setting, camera angle, product configuration, and reader decision across the set. Save assets under the current slug only; never reuse another topic's files unless the user explicitly requests a shared brand asset.

## Recommended Set

Choose roles that teach or support the article rather than decorating it:

1. Hero showing the complete product and realistic use environment.
2. Scale, seating, room-fit, or circulation context.
3. Material, width, edge, construction, or feature detail.
4. Working configuration with relevant accessories or technology.
5. Shape, finish, or design comparison.
6. Installation, delivery, support, base, or access context when relevant.
7. Closing visualization aligned with the CTA.

Do not invent a visual claim that the article cannot support. A generated render is not evidence for dimensions, structural capacity, code compliance, accessibility compliance, manufacturing capability, or a completed customer project.

## Prompt Requirements

Each prompt should specify:

- intended article section and teaching purpose;
- product, material, room, and use context;
- camera angle and an ultra-wide 12:5 composition;
- realistic proportions, construction, and lighting;
- complete product visibility with useful negative space;
- no people unless they are necessary to explain the topic;
- no logos, captions, measurements, readable screens, watermarks, or customer branding;
- no malformed furniture, duplicated objects, impossible geometry, or misleading details;
- original design concept, not a claimed customer installation.

Use photorealistic product or architectural visualization for furniture and buying-guide topics unless the subject clearly needs another visual form.

## Confirmed Tabletop-to-Base Geometry

Apply the following product-visual rules whenever a generated image shows the table base:

- For a rectangular or clearly elongated tabletop, show two separate black square-tube metal three-prong base assemblies positioned near the two ends. Each assembly must have exactly three vertical supports. At both the top and the floor, three square-tube arms must branch from one central junction in a visible Y-shaped / three-prong geometry. Treat an elongated oval tabletop the same way unless verified product information specifies another base. Do not simplify this into an inverted-U leg, rectangular loop frame, four-leg trestle, or one centered cross pedestal.
- For a round tabletop, show one centered black metal four-way cross base. The four vertical frame sections must extend symmetrically from the center beneath the round top. Do not use two separate end-frame bases.
- For a square, coffee, or other special tabletop without verified base information, do not infer either configuration. Mark the base choice as unverified in the visual brief and review.

State the tabletop shape, number of base assemblies, three vertical supports per assembly, top-and-bottom Y branching, base position, and black square-tube construction explicitly in every applicable prompt. Compare the result against the user-approved base reference image during visual review. Reject ordinary inverted-U or rectangular loop legs, as well as any shape/base mismatch, extra legs, floating joints, duplicated members, asymmetric branches, impossible connections, or hybrid of the rectangular-table and round-table systems.

## Mandatory Prompt Shell

Use this exact prompt shell once per selected image. Replace every `{...}` field
from the current topic's visual brief; do not reuse values from another topic.
The shell is deliberately fixed so image generation is never skipped, while the
subject, scene, camera, and teaching purpose still change with the article.

```text
Create one original AI design visualization for the Shopify SEO article
"{article topic}". Image role: {image role}. It must help the reader understand
the section "{target H2}" by showing {teaching purpose}. Depict {product or
subject} made from {material or finish} in {room, setting, or use context}.
Composition: {camera angle}, complete subject visible, ultra-wide 12:5 frame,
useful negative space, realistic scale, credible construction, and {lighting}.
Visual style: {photorealistic product or architectural visualization style}.
This is an original illustrative design concept, not a customer project or
technical drawing. Do not include people unless required to explain the section.
No logos, brand marks, captions, measurements, readable screens, watermarks,
text artifacts, malformed objects, duplicated furniture, impossible geometry,
or unsupported performance claims.
```

Before writing either DOCX, confirm in the task log that the image-generation
tool was called once for each selected asset and that every selected result is
saved locally. A completed prompt alone is not evidence that an image exists.

## Asset Pipeline

For every selected image:

1. Visually inspect the generated result at full resolution.
2. Copy the selected output into `<output-directory>/images/<slug>/`.
3. Center-crop to a 12:5 frame when needed, then resize to exactly 1200 x 500 pixels. Preserve aspect ratio; never stretch.
4. Use a descriptive lowercase hyphenated PNG or JPEG filename.
5. Insert the same local path at the corresponding location in both Markdown files and both language HTML files.
6. Write natural, language-specific alt text that explains what the image helps the reader inspect.
7. Build both DOCX files only after every local image exists and the task log
   records one image-generation call for each selected asset.
8. Render the DOCX files and inspect every image for visibility, distortion, cropping, caption pairing, and page flow.

Never leave a project-referenced asset only under a model-output or temporary directory.

## Metadata

Add this top-level object:

```json
{
  "imageGeneration": {
    "required": true,
    "sourceType": "ai-generated-original",
    "generatedCount": 7,
    "disclosure": "Original AI design visualizations; not customer-project photography."
  }
}
```

Every `imagePlan` item must include `imagePurpose`, `imagePrompt`, `fileName`, `localPath`, `altText`, `insertAfterHeading`, `imageRatio`, `sourceType`, and `status`. Use `imageRatio: 1200:500`, `sourceType: ai-generated-original`, and `status: generated` only after the asset exists and passes visual review.

Also include `visualBrief` in metadata with the topic, audience, visual style, and the section-to-image rationale so later revisions can regenerate the right set for that specific topic.

## Final Gate

Block delivery when any required image is missing, remote-only, duplicated, a neutral placeholder, not exactly 1200 x 500 pixels, absent from either language, omitted from either DOCX, visibly distorted, or presented as a real project. The bundle validator enforces the structural parts of this gate; visual review remains mandatory.
