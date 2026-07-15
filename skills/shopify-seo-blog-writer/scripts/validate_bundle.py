#!/usr/bin/env python3
"""Validate a bilingual Shopify SEO blog bundle using only the standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
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
    "word/_rels/document.xml.rels",
}
PLACEHOLDER_SHA256 = "f0417bb27a7cdfbc6e15f5f63b1a8d0419c1d9fa2cbafe697e8898c8095ef945"
IMAGE_PATTERN = re.compile(r"^!\[([^\]]*)\]\((.+)\)\s*$", flags=re.MULTILINE)
BLACK_TEXT_COLOR = "000000"
FORBIDDEN_DOCX_PHRASES = (
    "SHOPIFY SEO EDITORIAL DRAFT",
    "ENGLISH PUBLISH SOURCE",
    "DESIGN INSPIRATION",
    "PLANNED IMAGE",
)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path.name} must be UTF-8: {exc}") from exc


def markdown_images(text: str) -> list[tuple[str, str]]:
    images: list[tuple[str, str]] = []
    for alt_text, raw_source in IMAGE_PATTERN.findall(text):
        source = raw_source.strip()
        if source.startswith("<") and source.endswith(">"):
            source = source[1:-1]
        else:
            source = source.split(maxsplit=1)[0]
        images.append((alt_text.strip(), source))
    return images


def raster_dimensions(payload: bytes) -> tuple[int, int] | None:
    if payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 24:
        return struct.unpack(">II", payload[16:24])
    if not payload.startswith(b"\xff\xd8"):
        return None

    index = 2
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while index + 4 <= len(payload):
        if payload[index] != 0xFF:
            index += 1
            continue
        while index < len(payload) and payload[index] == 0xFF:
            index += 1
        if index >= len(payload):
            break
        marker = payload[index]
        index += 1
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(payload):
            break
        segment_length = struct.unpack(">H", payload[index : index + 2])[0]
        if segment_length < 2 or index + segment_length > len(payload):
            break
        if marker in sof_markers and segment_length >= 7:
            height, width = struct.unpack(">HH", payload[index + 3 : index + 7])
            return width, height
        index += segment_length
    return None


def validate_image_assets(
    label: str,
    markdown_path: Path,
    text: str,
    errors: list[str],
) -> list[str]:
    image_refs = markdown_images(text)
    sources: list[str] = []
    for index, (alt_text, source) in enumerate(image_refs, start=1):
        if not alt_text:
            errors.append(f"{label}: image {index} must have descriptive alt text")
        if source.startswith(("http://", "https://")):
            errors.append(
                f"{label}: image {index} must be downloaded as a local asset before DOCX generation"
            )
            sources.append(source)
            continue

        path = Path(source).expanduser()
        if not path.is_absolute():
            path = markdown_path.parent / path
        sources.append(source)
        if not path.is_file():
            errors.append(f"{label}: image {index} is missing: {path}")
            continue
        try:
            payload = path.read_bytes()
        except OSError as exc:
            errors.append(f"{label}: image {index} cannot be read: {exc}")
            continue
        if hashlib.sha256(payload).hexdigest() == PLACEHOLDER_SHA256:
            errors.append(f"{label}: image {index} is the neutral placeholder, not a finished asset")
            continue
        dimensions = raster_dimensions(payload)
        if dimensions is None:
            errors.append(f"{label}: image {index} must be a valid PNG or JPEG file")
        elif dimensions != (1200, 500):
            errors.append(
                f"{label}: image {index} must be exactly 1200 x 500 pixels, found "
                f"{dimensions[0]} x {dimensions[1]}"
            )

    if len(set(sources)) != len(sources):
        errors.append(f"{label}: every placement must use a distinct original image asset")
    return sources


def markdown_metrics(text: str) -> dict[str, Any]:
    h1 = re.findall(r"^# (.+)$", text, flags=re.MULTILINE)
    h2 = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
    images = markdown_images(text)
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
    elif images:
        required_image_fields = {
            "imagePurpose",
            "imagePrompt",
            "fileName",
            "localPath",
            "altText",
            "insertAfterHeading",
            "imageRatio",
            "sourceType",
            "status",
        }
        for index, item in enumerate(images, start=1):
            if not isinstance(item, dict):
                errors.append(f"meta: imagePlan item {index} must be an object")
                continue
            missing_fields = sorted(
                field for field in required_image_fields if not str(item.get(field, "")).strip()
            )
            if missing_fields:
                errors.append(
                    f"meta: imagePlan item {index} is missing fields {missing_fields}"
                )
            if item.get("sourceType") != "ai-generated-original":
                errors.append(
                    f"meta: imagePlan item {index} sourceType must be 'ai-generated-original'"
                )
            if item.get("status") != "generated":
                errors.append(f"meta: imagePlan item {index} status must be 'generated'")
            if item.get("imageRatio") != "1200:500":
                errors.append(f"meta: imagePlan item {index} imageRatio must be '1200:500'")

    image_generation = meta.get("imageGeneration")
    if not isinstance(image_generation, dict):
        errors.append("meta: imageGeneration object is required")
    else:
        if image_generation.get("required") is not True:
            errors.append("meta: imageGeneration.required must be true")
        if image_generation.get("sourceType") != "ai-generated-original":
            errors.append(
                "meta: imageGeneration.sourceType must be 'ai-generated-original'"
            )
        generated_count = image_generation.get("generatedCount")
        if not isinstance(generated_count, int) or generated_count < 5:
            errors.append("meta: imageGeneration.generatedCount must be at least 5")

    visual_brief = meta.get("visualBrief")
    if not isinstance(visual_brief, dict):
        errors.append("meta: visualBrief object is required")
    else:
        for key in ("topic", "audience", "visualStyle", "sectionRationale"):
            if not str(visual_brief.get(key, "")).strip():
                errors.append(f"meta: visualBrief.{key} is required")

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
            styles_payload = archive.read("word/styles.xml")
            styles = ET.fromstring(styles_payload)
            media_names = [
                name
                for name in archive.namelist()
                if name.startswith("word/media/") and not name.endswith("/")
            ]
            media_payloads = [archive.read(name) for name in media_names]
            media_count = len(media_names)
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
    if "Image pending" in document_text or "图片待补" in document_text:
        errors.append(f"{label}: contains an image placeholder instead of a finished asset")
    for forbidden in FORBIDDEN_DOCX_PHRASES:
        if forbidden in document_text:
            errors.append(
                f"{label}: contains forbidden template text {forbidden!r}; rebuild with the locked V4 buying-guide master"
            )
            break

    # The approved preview uses black text only. Inspect all text-bearing parts.
    for part_name, root in (("document", document), ("styles", styles)):
        for color in root.findall(".//w:color", namespace):
            value = str(color.get(f"{{{WORD_NAMESPACE}}}val", "")).upper()
            uses_theme = any(
                color.get(f"{{{WORD_NAMESPACE}}}{attribute}")
                for attribute in ("themeColor", "themeTint", "themeShade")
            )
            if value != BLACK_TEXT_COLOR or uses_theme:
                errors.append(
                    f"{label}: {part_name} text color must be #000000 without a theme color"
                )
                break

    title_styles = document.findall(".//w:pStyle[@w:val='Title']", namespace)
    heading_styles = document.findall(".//w:pStyle[@w:val='Heading1']", namespace)
    if not title_styles and not heading_styles:
        errors.append(f"{label}: expected a real Word Title or Heading 1 style")

    if document.find(".//w:headerReference", namespace) is not None:
        errors.append(f"{label}: headers are not allowed")
    if document.find(".//w:footerReference", namespace) is not None:
        errors.append(f"{label}: footers are not allowed")
    if any(name.startswith("word/header") or name.startswith("word/footer") for name in archive.namelist()):
        errors.append(f"{label}: DOCX package must not contain header or footer parts")

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
    if any(
        hashlib.sha256(payload).hexdigest() == PLACEHOLDER_SHA256
        for payload in media_payloads
    ):
        errors.append(f"{label}: DOCX media package contains the neutral placeholder image")
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

    normal_style = styles.find(".//w:style[@w:styleId='Normal']", namespace)
    if normal_style is None:
        errors.append(f"{label}: missing Normal style")
    else:
        normal_fonts = normal_style.find(".//w:rFonts", namespace)
        normal_size = normal_style.find(".//w:sz", namespace)
        if normal_fonts is None or normal_fonts.get(f"{{{WORD_NAMESPACE}}}ascii") != "Calibri":
            errors.append(f"{label}: body font must be Calibri")
        if normal_size is None or normal_size.get(f"{{{WORD_NAMESPACE}}}val") != "21":
            errors.append(f"{label}: body font size must be 10.5 pt (五号)")

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
    english_image_sources = validate_image_assets(
        "English Markdown",
        files["English Markdown"],
        en_md,
        errors,
    )
    chinese_image_sources = validate_image_assets(
        "Chinese Markdown",
        files["Chinese Markdown"],
        zh_md,
        errors,
    )
    if english_image_sources != chinese_image_sources:
        errors.append(
            "Bilingual images: English and Chinese Markdown must use the same local assets in the same order"
        )
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
