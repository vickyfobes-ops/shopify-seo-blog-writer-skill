#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import binascii
import json
import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "shopify-seo-blog-writer" / "scripts" / "validate_bundle.py"
SPEC = importlib.util.spec_from_file_location("validate_bundle", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BUILD_SCRIPT = Path(__file__).parents[1] / "skills" / "shopify-seo-blog-writer" / "scripts" / "build_docx.py"
BUILD_SPEC = importlib.util.spec_from_file_location("build_docx", BUILD_SCRIPT)
assert BUILD_SPEC and BUILD_SPEC.loader
BUILD_MODULE = importlib.util.module_from_spec(BUILD_SPEC)
BUILD_SPEC.loader.exec_module(BUILD_MODULE)


def sample_render_png(width: int = 1200, height: int = 500) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
        )

    rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            row.extend(((x * 7 + y) % 256, (x + y * 3) % 256, (x * 2 + y * 5) % 256))
        rows.append(b"\x00" + bytes(row))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(b"".join(rows), level=9))
        + chunk(b"IEND", b"")
    )


def generated_image_plan(count: int = 5) -> list[dict[str, str]]:
    return [
        {
            "imagePurpose": f"Support section {index}",
            "imagePrompt": f"Original product render {index}",
            "fileName": f"image-{index}.png",
            "localPath": f"images/image-{index}.png",
            "altText": f"Original AI design render {index}",
            "insertAfterHeading": f"Section {index}",
            "imageRatio": "1200:500",
            "sourceType": "ai-generated-original",
            "status": "generated",
        }
        for index in range(1, count + 1)
    ]


class ValidateBundleTests(unittest.TestCase):
    def test_required_files_include_bilingual_docx(self) -> None:
        files = MODULE.bundle_files(Path("/tmp/output"), "epoxy-table-guide")
        self.assertEqual(files["English DOCX"].name, "epoxy-table-guide.en.docx")
        self.assertEqual(files["Chinese DOCX"].name, "epoxy-table-guide.zh-CN.docx")

    def test_docx_builder_creates_complete_word_package(self) -> None:
        markdown = """# Epoxy Conference Table Guide

Choose a table after checking room dimensions and daily seating needs.

## Recommended Size

- Allow **30 inches** per person.
- Verify [planning guidance](https://example.com/planning).

| Seats | Length |
| --- | --- |
| 8 | 96 inches |

![Conference table dimensions](conference-table.png)
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output = directory / "guide.en.docx"
            image = directory / "conference-table.png"
            image.write_bytes(sample_render_png())
            metadata = {
                "keyword": "epoxy conference table guide",
                "searchIntent": "commercial investigation / office planning",
                "seo": {
                    "seoTitle": "Epoxy Conference Table Guide: Sizes and Room Fit",
                    "urlHandle": "epoxy-conference-table-guide",
                },
            }
            BUILD_MODULE.build_docx(
                markdown,
                output,
                "en-US",
                source_dir=directory,
                metadata=metadata,
            )
            errors: list[str] = []
            warnings: list[str] = []
            MODULE.validate_docx("English DOCX", output, markdown, errors, warnings)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            self.assertGreater(output.stat().st_size, 2_000)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                document_xml = archive.read("word/document.xml").decode("utf-8")
                styles_xml = archive.read("word/styles.xml").decode("utf-8")
                self.assertIn("word/media/image1.png", names)
                self.assertIn("Primary keyword", document_xml)
                self.assertIn("epoxy-conference-table-guide", document_xml)
                self.assertNotIn("word/header1.xml", names)
                self.assertNotIn("word/footer1.xml", names)
                self.assertIn('styleId="Normal"', styles_xml)
                self.assertIn('w:ascii="Calibri"', styles_xml)
                self.assertIn('w:sz w:val="21"', styles_xml)

    def test_chinese_docx_uses_localized_v4_labels_and_cjk_font(self) -> None:
        markdown = """# 环氧树脂会议桌尺寸指南

![会议桌尺寸示例](missing.png)

先测量房间，再选择桌面。

## 建议尺寸

每天每人预留 30 英寸有效桌边。
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output = directory / "guide.zh-CN.docx"
            (directory / "missing.png").write_bytes(sample_render_png())
            BUILD_MODULE.build_docx(
                markdown,
                output,
                "zh-CN",
                source_dir=directory,
            )
            errors: list[str] = []
            warnings: list[str] = []
            MODULE.validate_docx("Chinese DOCX", output, markdown, errors, warnings)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            with zipfile.ZipFile(output) as archive:
                styles_xml = archive.read("word/styles.xml").decode("utf-8")
                document_xml = archive.read("word/document.xml").decode("utf-8")
                self.assertNotIn("word/header1.xml", archive.namelist())
                self.assertNotIn("word/footer1.xml", archive.namelist())
                self.assertIn(BUILD_MODULE.CJK_FONT, styles_xml)
                self.assertNotIn("图片待补", document_xml)

    def test_docx_builder_rejects_missing_images_by_default(self) -> None:
        markdown = "# Guide\n\n![Original AI design render](missing.png)\n"
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "guide.en.docx"
            with self.assertRaisesRegex(ValueError, "image is missing or unreadable"):
                BUILD_MODULE.build_docx(markdown, output, "en-US")

    def test_image_asset_validator_rejects_neutral_placeholder(self) -> None:
        markdown = "# Guide\n\n![Original AI design render](placeholder.png)\n"
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            source = directory / "guide.md"
            source.write_text(markdown, encoding="utf-8")
            (directory / "placeholder.png").write_bytes(BUILD_MODULE.placeholder_png())
            errors: list[str] = []
            MODULE.validate_image_assets("English Markdown", source, markdown, errors)
            self.assertTrue(any("neutral placeholder" in error for error in errors))

    def test_docx_validator_rejects_plain_text_with_docx_extension(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "broken.docx"
            output.write_text("not a Word package", encoding="utf-8")
            errors: list[str] = []
            warnings: list[str] = []
            MODULE.validate_docx("English DOCX", output, "# Title", errors, warnings)
            self.assertTrue(any("not a valid DOCX" in error for error in errors))

    def test_docx_validator_rejects_nonblack_or_theme_text(self) -> None:
        markdown = "# Guide\n\nA black-text document.\n"
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output = directory / "guide.en.docx"
            BUILD_MODULE.build_docx(markdown, output, "en-US", source_dir=directory)
            with zipfile.ZipFile(output) as archive:
                members = {name: archive.read(name) for name in archive.namelist()}
            members["word/styles.xml"] = members["word/styles.xml"].replace(
                b'val="000000"', b'val="4472C4" themeColor="accent1"', 1
            )
            with zipfile.ZipFile(output, "w") as archive:
                for name, payload in members.items():
                    archive.writestr(name, payload)
            errors: list[str] = []
            warnings: list[str] = []
            MODULE.validate_docx("English DOCX", output, markdown, errors, warnings)
            self.assertTrue(any("text color must be #000000" in error for error in errors))

    def test_docx_validator_rejects_magazine_template_text(self) -> None:
        markdown = "# Guide\n\nBody copy.\n"
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output = directory / "guide.en.docx"
            BUILD_MODULE.build_docx(markdown, output, "en-US", source_dir=directory)
            with zipfile.ZipFile(output) as archive:
                members = {name: archive.read(name) for name in archive.namelist()}
            members["word/document.xml"] = members["word/document.xml"].replace(
                b"Guide", b"DESIGN INSPIRATION", 1
            )
            with zipfile.ZipFile(output, "w") as archive:
                for name, payload in members.items():
                    archive.writestr(name, payload)
            errors: list[str] = []
            warnings: list[str] = []
            MODULE.validate_docx("English DOCX", output, markdown, errors, warnings)
            self.assertTrue(any("forbidden template text" in error for error in errors))

    def test_markdown_metrics_for_valid_shape(self) -> None:
        sections = "\n".join(f"## Section {index}\nBody" for index in range(1, 6))
        images = "\n".join(f"![Alt {index}](image-{index}.jpg)" for index in range(1, 6))
        sources = "\n".join(
            f"- [Source {index}](https://example.com/{index})" for index in range(1, 4)
        )
        faqs = "\n".join(f"### Question {index}?\nAnswer." for index in range(1, 5))
        markdown = (
            f"# Title\n{images}\n{sections}\n## Frequently Asked Questions\n"
            f"{faqs}\n### What sources support this article?\n{sources}\n"
        )
        metrics = MODULE.markdown_metrics(markdown)
        self.assertEqual(metrics["h1"], 1)
        self.assertEqual(metrics["h2"], 6)
        self.assertEqual(metrics["faq"], 5)
        self.assertEqual(metrics["images"], 5)
        self.assertEqual(metrics["sources_at_end"], 3)

    def test_meta_validation_accepts_safe_defaults(self) -> None:
        slug = "epoxy-table-guide"
        meta = {
            "topic": "Epoxy table guide",
            "keyword": "epoxy table guide",
            "searchIntent": "commercial investigation",
            "researchSources": [
                {"url": f"https://example.com/{index}"} for index in range(3)
            ],
            "seo": {
                "seoTitle": "Epoxy Table Guide: Sizes, Uses, and Buying Tips",
                "metaDescription": "Use this epoxy table guide to compare practical sizes, materials, room fit, maintenance, delivery needs, and buying questions before ordering.",
                "urlHandle": slug,
            },
            "imageGeneration": {
                "required": True,
                "sourceType": "ai-generated-original",
                "generatedCount": 5,
            },
            "visualBrief": {
                "topic": "Epoxy table guide",
                "audience": "buyers",
                "visualStyle": "photorealistic product render",
                "sectionRationale": "One distinct original render for each buying decision.",
            },
            "imagePlan": generated_image_plan(),
            "selfReview": {
                "seoScoreType": "Internal on-page readiness score, not a ranking guarantee"
            },
            "shopify": {"apiCalled": False, "draftCreated": False, "published": False},
        }
        errors: list[str] = []
        warnings: list[str] = []
        MODULE.validate_meta(meta, slug, slug, errors, warnings)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_versioned_filename_can_use_canonical_handle(self) -> None:
        slug = "epoxy-table-guide-v5"
        handle = "epoxy-table-guide"
        meta = {
            "topic": "Epoxy table guide",
            "keyword": "epoxy table guide",
            "searchIntent": "commercial investigation",
            "researchSources": [
                {"url": f"https://example.com/{index}"} for index in range(3)
            ],
            "seo": {
                "seoTitle": "Epoxy Table Guide: Sizes, Uses, and Buying Tips",
                "metaDescription": "Use this epoxy table guide to compare practical sizes, materials, room fit, maintenance, delivery needs, and buying questions before ordering.",
                "urlHandle": handle,
            },
            "imageGeneration": {
                "required": True,
                "sourceType": "ai-generated-original",
                "generatedCount": 5,
            },
            "visualBrief": {
                "topic": "Epoxy table guide",
                "audience": "buyers",
                "visualStyle": "photorealistic product render",
                "sectionRationale": "One distinct original render for each buying decision.",
            },
            "imagePlan": generated_image_plan(),
            "selfReview": {
                "seoScoreType": "Internal on-page readiness score, not a ranking guarantee"
            },
            "shopify": {"apiCalled": False, "draftCreated": False, "published": False},
        }
        errors: list[str] = []
        warnings: list[str] = []
        MODULE.validate_meta(meta, slug, handle, errors, warnings)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
