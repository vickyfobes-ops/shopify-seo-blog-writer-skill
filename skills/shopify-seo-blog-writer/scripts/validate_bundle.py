#!/usr/bin/env python3
"""Validate a bilingual Shopify SEO blog bundle using only the standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


FAQ_HEADINGS = {
    "Frequently Asked Questions",
    "FAQ",
    "常见问题",
}

WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WORD_DRAWING_NAMESPACE = (
    "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
)
DOCX_REQUIRED_PARTS = {
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml",
    "word/styles.xml",
    "word/header1.xml",
    "word/footer1.xml",
    "word/_rels/document.xml.rels",
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


def normalized_content(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return "".join(re.findall(r"[A-Za-z0-9\u3400-\u9fff]+", text))


def validate_docx(
    label: str,
    path: Path,
    source_markdown: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    if not zipfile.is_zipfile(path):
        errors.append(f"{label}: not a valid DOCX/ZIP package")
        return

    try:
        with zipfile.ZipFile(path) as archive:
            missing_parts = sorted(DOCX_REQUIRED_PARTS.difference(archive.namelist()))
            if missing_parts:
                errors.append(f"{label}: missing DOCX package parts {missing_parts}")
                return
            damaged_member = archive.testzip()
            if damaged_member:
                errors.append(f"{label}: corrupt ZIP member {damaged_member!r}")
                return
            document = ET.fromstring(archive.read("word/document.xml"))
            header = ET.fromstring(archive.read("word/header1.xml"))
            footer = ET.fromstring(archive.read("word/footer1.xml"))
            styles_payload = archive.read("word/styles.xml")
            styles = ET.fromstring(styles_payload)
            media_count = len(
                [
                    name
                    for name in archive.namelist()
                    if name.startswith("word/media/") and not name.endswith("/")
                ]
            )
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        errors.append(f"{label}: cannot read DOCX structure: {exc}")
        return

    namespace = {
        "w": WORD_NAMESPACE,
        "wp": WORD_DRAWING_NAMESPACE,
    }
    document_text = "".join(node.text or "" for node in document.findall(".//w:t", namespace))
    if not document_text.strip():
        errors.append(f"{label}: document.xml contains no readable text")
        return

    title_styles = document.findall(".//w:pStyle[@w:val='Title']", namespace)
    heading_styles = document.findall(".//w:pStyle[@w:val='Heading1']", namespace)
    if not title_styles and not heading_styles:
        errors.append(f"{label}: expected a real Word Title or Heading 1 style")

    if document.find(".//w:headerReference", namespace) is None:
        errors.append(f"{label}: missing section header reference")
    if document.find(".//w:footerReference", namespace) is None:
        errors.append(f"{label}: missing section footer reference")

    header_text = "".join(node.text or "" for node in header.findall(".//w:t", namespace))
    footer_text = "".join(node.text or "" for node in footer.findall(".//w:t", namespace))
    footer_fields = "".join(
        node.text or "" for node in footer.findall(".//w:instrText", namespace)
    )
    chinese = "chinese" in label.lower() or "zh-cn" in label.lower()
    if "SHOPIFY BLOG" not in header_text:
        errors.append(f"{label}: header must identify the local Shopify blog draft")
    if chinese:
        if "草稿" not in header_text:
            errors.append(f"{label}: Chinese header must include 草稿")
        if "未发布" not in footer_text:
            errors.append(f"{label}: Chinese footer must state 未发布")
    else:
        if "DRAFT" not in header_text:
            errors.append(f"{label}: English header must include DRAFT")
        if "not published" not in footer_text.lower():
            errors.append(f"{label}: English footer must state not published")
    if "PAGE" not in footer_fields:
        errors.append(f"{label}: footer must contain an automatic PAGE field")

    section = document.find(".//w:sectPr", namespace)
    if section is None:
        errors.append(f"{label}: missing section page setup")
    else:
        page_size = section.find("w:pgSz", namespace)
        expected_size = {"w": "12240", "h": "15840"}
        if page_size is None or any(
            page_size.get(f"{{{WORD_NAMESPACE}}}{key}") != value
            for key, value in expected_size.items()
        ):
            errors.append(f"{label}: page size must be US Letter portrait")
        margins = section.find("w:pgMar", namespace)
        expected_margins = {
            "top": "1440",
            "right": "1440",
            "bottom": "1440",
            "left": "1440",
        }
        if margins is None or any(
            margins.get(f"{{{WORD_NAMESPACE}}}{key}") != value
            for key, value in expected_margins.items()
        ):
            errors.append(f"{label}: page margins must be one inch on every side")

    tables = document.findall(".//w:tbl", namespace)
    if not tables:
        errors.append(f"{label}: missing first-page SEO metadata table")
    else:
        metadata_rows = tables[0].findall("w:tr", namespace)
        first_row_cells = (
            metadata_rows[0].findall("w:tc", namespace) if metadata_rows else []
        )
        if len(metadata_rows) < 5 or len(first_row_cells) != 2:
            errors.append(
                f"{label}: first table must be the five-row, two-column SEO metadata table"
            )

    expected_images = markdown_metrics(source_markdown)["images"]
    drawings = document.findall(".//w:drawing", namespace)
    if len(drawings) != expected_images:
        errors.append(
            f"{label}: expected {expected_images} embedded image(s), found {len(drawings)}"
        )
    if media_count < len(drawings):
        errors.append(
            f"{label}: DOCX media package has {media_count} file(s) for {len(drawings)} drawing(s)"
        )
    image_properties = document.findall(".//wp:docPr", namespace)
    if len(image_properties) != len(drawings) or any(
        not str(item.get("descr", "")).strip() for item in image_properties
    ):
        errors.append(f"{label}: every embedded image must retain descriptive alt text")
    for extent in document.findall(".//wp:extent", namespace):
        if (
            extent.get("cx") != "5623560"
            or extent.get("cy") != "2343150"
        ):
            errors.append(
                f"{label}: every image must use the V4 6.15 x 2.5625-inch frame"
            )
            break

    east_asia_fonts = {
        str(font.get(f"{{{WORD_NAMESPACE}}}eastAsia", "")).strip()
        for font in styles.findall(".//w:rFonts", namespace)
    }
    east_asia_fonts.discard("")
    if not east_asia_fonts or east_asia_fonts.issubset({"Calibri", "Arial", "Aptos"}):
        errors.append(f"{label}: styles must include a dedicated CJK-capable font")

    source_content = normalized_content(source_markdown)
    docx_content = normalized_content(document_text)
    if source_content:
        completeness = len(docx_content) / len(source_content)
        if completeness < 0.85:
            errors.append(
                f"{label}: DOCX text appears incomplete versus Markdown "
                f"({completeness:.0%} retained)"
            )
        elif completeness < 0.95:
            warnings.append(
                f"{label}: verify DOCX text parity with Markdown ({completeness:.0%} retained)"
            )


def bundle_files(directory: Path, slug: str) -> dict[str, Path]:
    return {
        "English DOCX": directory / f"{slug}.en.docx",
        "Chinese DOCX": directory / f"{slug}.zh-CN.docx",
        "English Markdown": directory / f"{slug}.md",
        "Chinese Markdown": directory / f"{slug}.zh-CN.md",
        "English HTML": directory / f"{slug}.html",
        "Chinese HTML": directory / f"{slug}.zh-CN.html",
        "Bilingual HTML": directory / f"{slug}.bilingual.html",
        "Metadata": directory / f"{slug}.meta.json",
        "Review": directory / f"{slug}.review.md",
    }


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
    files = bundle_files(directory, slug)

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
    validate_docx("English DOCX", files["English DOCX"], en_md, errors, warnings)
    validate_docx("Chinese DOCX", files["Chinese DOCX"], zh_md, errors, warnings)
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
