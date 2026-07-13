#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
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
            image.write_bytes(BUILD_MODULE.placeholder_png())
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
                header_xml = archive.read("word/header1.xml").decode("utf-8")
                footer_xml = archive.read("word/footer1.xml").decode("utf-8")
                self.assertIn("word/media/image1.png", names)
                self.assertIn("Primary keyword", document_xml)
                self.assertIn("epoxy-conference-table-guide", document_xml)
                self.assertIn("OFFICE PLANNING GUIDE", header_xml)
                self.assertIn("not published", footer_xml)
                self.assertIn(" PAGE ", footer_xml)

    def test_chinese_docx_uses_localized_v4_labels_and_cjk_font(self) -> None:
        markdown = """# 环氧树脂会议桌尺寸指南

![会议桌尺寸示例](missing.png)

先测量房间，再选择桌面。

## 建议尺寸

每天每人预留 30 英寸有效桌边。
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "guide.zh-CN.docx"
            BUILD_MODULE.build_docx(markdown, output, "zh-CN")
            errors: list[str] = []
            warnings: list[str] = []
            MODULE.validate_docx("Chinese DOCX", output, markdown, errors, warnings)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            with zipfile.ZipFile(output) as archive:
                header_xml = archive.read("word/header1.xml").decode("utf-8")
                footer_xml = archive.read("word/footer1.xml").decode("utf-8")
                styles_xml = archive.read("word/styles.xml").decode("utf-8")
                document_xml = archive.read("word/document.xml").decode("utf-8")
                self.assertIn("SHOPIFY BLOG 草稿", header_xml)
                self.assertIn("未发布", footer_xml)
                self.assertIn(BUILD_MODULE.CJK_FONT, styles_xml)
                self.assertIn("图片待补", document_xml)

    def test_docx_validator_rejects_plain_text_with_docx_extension(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "broken.docx"
            output.write_text("not a Word package", encoding="utf-8")
            errors: list[str] = []
            warnings: list[str] = []
            MODULE.validate_docx("English DOCX", output, "# Title", errors, warnings)
            self.assertTrue(any("not a valid DOCX" in error for error in errors))

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
            "imagePlan": [{} for _ in range(5)],
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
            "imagePlan": [{} for _ in range(5)],
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
