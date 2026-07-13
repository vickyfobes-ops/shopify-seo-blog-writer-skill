#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "shopify-seo-blog-writer" / "scripts" / "validate_bundle.py"
SPEC = importlib.util.spec_from_file_location("validate_bundle", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ValidateBundleTests(unittest.TestCase):
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
