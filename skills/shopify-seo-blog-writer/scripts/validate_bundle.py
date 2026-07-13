#!/usr/bin/env python3
"""Validate a bilingual Shopify SEO blog bundle using only the standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


FAQ_HEADINGS = {
    "Frequently Asked Questions",
    "FAQ",
    "常见问题",
}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path.name} must be UTF-8: {exc}") from exc


def markdown_metrics(text: str) -> dict[str, Any]:
    h1 = re.findall(r"^# (.+)$", text, flags=re.MULTILINE)
    h2 = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
    images = re.findall(r"^!\[[^\]]*\]\([^\)]+\)", text, flags=re.MULTILINE)
    final_h2 = h2[-1].strip() if h2 else ""
    faq_part = re.split(r"^## .+$", text, flags=re.MULTILINE)[-1] if h2 else ""
    faqs = re.findall(r"^### (.+)$", faq_part, flags=re.MULTILINE)
    external_links = re.findall(r"\[[^\]]+\]\((https?://[^\)]+)\)", faq_part)
    return {
        "h1": len(h1),
        "h2": len(h2),
        "final_h2": final_h2,
        "faq": len(faqs),
        "images": len(images),
        "sources_at_end": len(external_links),
    }


def nested(data: dict[str, Any], *keys: str) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def validate_markdown(label: str, text: str, errors: list[str], warnings: list[str]) -> None:
    metrics = markdown_metrics(text)
    if metrics["h1"] != 1:
        errors.append(f"{label}: expected exactly 1 H1, found {metrics['h1']}")
    if not 6 <= metrics["h2"] <= 10:
        warnings.append(f"{label}: expected 6-10 H2 sections, found {metrics['h2']}")
    if metrics["final_h2"] not in FAQ_HEADINGS:
        errors.append(f"{label}: final H2 must be FAQ, found {metrics['final_h2']!r}")
    if metrics["faq"] != 5:
        errors.append(f"{label}: expected exactly 5 FAQ questions, found {metrics['faq']}")
    if metrics["images"] < 5:
        errors.append(f"{label}: expected at least 5 image placements, found {metrics['images']}")
    if metrics["sources_at_end"] < 3:
        errors.append(
            f"{label}: expected at least 3 external source links in the final FAQ answer, "
            f"found {metrics['sources_at_end']}"
        )


def validate_meta(
    meta: dict[str, Any],
    slug: str,
    canonical_handle: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    required = ["keyword", "searchIntent", "researchSources", "seo", "imagePlan", "selfReview", "shopify"]
    for key in required:
        if key not in meta:
            errors.append(f"meta: missing required key {key!r}")
    if "topic" not in meta:
        warnings.append("meta: add the original user topic for traceability")

    title = nested(meta, "seo", "seoTitle")
    description = nested(meta, "seo", "metaDescription")
    handle = nested(meta, "seo", "urlHandle")
    if not isinstance(title, str) or not 45 <= len(title) <= 60:
        errors.append(f"meta: SEO title must be 45-60 characters, found {len(title) if isinstance(title, str) else 'missing'}")
    if not isinstance(description, str) or not 140 <= len(description) <= 160:
        errors.append(
            f"meta: meta description must be 140-160 characters, "
            f"found {len(description) if isinstance(description, str) else 'missing'}"
        )
    if handle != canonical_handle:
        errors.append(
            f"meta: urlHandle must equal canonical handle {canonical_handle!r}, found {handle!r}"
        )
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        errors.append(f"slug: must be lowercase hyphen-case, found {slug!r}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", canonical_handle):
        errors.append(f"handle: must be lowercase hyphen-case, found {canonical_handle!r}")

    sources = meta.get("researchSources")
    if not isinstance(sources, list) or len(sources) < 3:
        errors.append("meta: researchSources must contain at least 3 items")
    elif any(not isinstance(item, dict) or not str(item.get("url", "")).startswith("http") for item in sources):
        errors.append("meta: every research source must include an HTTP(S) URL")

    images = meta.get("imagePlan")
    if not isinstance(images, list) or len(images) < 5:
        errors.append("meta: imagePlan must contain at least 5 items")

    shopify = meta.get("shopify")
    if not isinstance(shopify, dict):
        errors.append("meta: shopify status object is required")
    else:
        for key in ("apiCalled", "draftCreated", "published"):
            if shopify.get(key) is not False:
                errors.append(f"meta: shopify.{key} must default to false")

    score_type = nested(meta, "selfReview", "seoScoreType")
    if not isinstance(score_type, str) or "not a ranking" not in score_type.lower():
        warnings.append("meta: clarify that the SEO score is not a ranking guarantee")


def validate_html(label: str, text: str, errors: list[str]) -> None:
    h1_count = len(re.findall(r"<h1(?:\s[^>]*)?>", text, flags=re.IGNORECASE))
    h2_values = [re.sub(r"<[^>]+>", "", value).strip() for value in re.findall(r"<h2(?:\s[^>]*)?>(.*?)</h2>", text, flags=re.IGNORECASE | re.DOTALL)]
    if h1_count != 1:
        errors.append(f"{label}: expected exactly 1 HTML H1, found {h1_count}")
    if not h2_values or h2_values[-1] not in FAQ_HEADINGS:
        errors.append(f"{label}: final HTML H2 must be FAQ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, type=Path, help="Directory containing the bundle")
    parser.add_argument("--slug", required=True, help="Lowercase hyphenated filename stem")
    parser.add_argument(
        "--handle",
        help="Canonical URL handle; defaults to the slug with a trailing -vN removed",
    )
    args = parser.parse_args()

    directory = args.dir.expanduser().resolve()
    slug = args.slug
    canonical_handle = args.handle or re.sub(r"-v\d+$", "", slug)
    files = {
        "English Markdown": directory / f"{slug}.md",
        "Chinese Markdown": directory / f"{slug}.zh-CN.md",
        "English HTML": directory / f"{slug}.html",
        "Chinese HTML": directory / f"{slug}.zh-CN.html",
        "Bilingual HTML": directory / f"{slug}.bilingual.html",
        "Metadata": directory / f"{slug}.meta.json",
        "Review": directory / f"{slug}.review.md",
    }

    errors: list[str] = []
    warnings: list[str] = []
    for label, path in files.items():
        if not path.is_file():
            errors.append(f"{label}: missing {path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    try:
        en_md = read(files["English Markdown"])
        zh_md = read(files["Chinese Markdown"])
        en_html = read(files["English HTML"])
        zh_html = read(files["Chinese HTML"])
        review = read(files["Review"])
        meta = json.loads(read(files["Metadata"]))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    validate_markdown("English Markdown", en_md, errors, warnings)
    validate_markdown("Chinese Markdown", zh_md, errors, warnings)
    validate_html("English HTML", en_html, errors)
    validate_html("Chinese HTML", zh_html, errors)
    validate_meta(meta, slug, canonical_handle, errors, warnings)

    if "Shopify API: Not called" not in review and "Shopify API：未调用" not in review:
        warnings.append("review: explicitly report that the Shopify API was not called")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS: bundle {slug!r} passed with {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
