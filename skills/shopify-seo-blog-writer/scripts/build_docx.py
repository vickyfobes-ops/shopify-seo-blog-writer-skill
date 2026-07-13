#!/usr/bin/env python3
"""Build the required V4-format DOCX from a Shopify SEO blog Markdown source.

The generator uses only the Python standard library. It creates a local,
unpublished editorial preview with bilingual labels, SEO front matter, embedded
images, real Word styles, tables, lists, links, headers, footers, and page fields.
"""

from __future__ import annotations

import argparse
import binascii
import datetime as dt
import html
import json
import re
import struct
import zipfile
import zlib
from pathlib import Path
from typing import Any
from urllib.parse import unquote
from xml.etree import ElementTree as ET


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DCTERMS = "http://purl.org/dc/terms/"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
EP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
VT = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
XML = "http://www.w3.org/XML/1998/namespace"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"

IMAGE_WIDTH_EMU = 5_623_560
IMAGE_HEIGHT_EMU = 2_343_150
TABLE_WIDTH_DXA = 9_360
LETTER_WIDTH_DXA = 12_240
LETTER_HEIGHT_DXA = 15_840
ONE_INCH_DXA = 1_440


def preferred_cjk_font() -> str:
    candidates = [
        (Path("C:/Windows/Fonts/msyh.ttc"), "Microsoft YaHei"),
        (Path("/System/Library/Fonts/STHeiti Medium.ttc"), "Heiti SC"),
        (
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            "Noto Sans CJK SC",
        ),
        (
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            "Noto Sans CJK SC",
        ),
        (
            Path("/usr/share/fonts/opentype/source-han-sans/SourceHanSansSC-Regular.otf"),
            "Source Han Sans SC",
        ),
        (
            Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
            "Arial Unicode MS",
        ),
    ]
    for path, family in candidates:
        if path.is_file():
            return family
    return "Microsoft YaHei"


CJK_FONT = preferred_cjk_font()


for prefix, uri in {
    "w": W,
    "r": R,
    "cp": CP,
    "dc": DC,
    "dcterms": DCTERMS,
    "xsi": XSI,
    "ep": EP,
    "vt": VT,
    "wp": WP,
    "a": A,
    "pic": PIC,
}.items():
    ET.register_namespace(prefix, uri)


def q(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def w(tag: str) -> str:
    return q(W, tag)


def add(parent: ET.Element, tag: str, attrs: dict[str, str] | None = None) -> ET.Element:
    return ET.SubElement(parent, w(tag), {w(key): value for key, value in (attrs or {}).items()})


def ns_add(
    parent: ET.Element,
    namespace: str,
    tag: str,
    attrs: dict[str, str] | None = None,
) -> ET.Element:
    return ET.SubElement(parent, q(namespace, tag), attrs or {})


def xml_bytes(root: ET.Element) -> bytes:
    payload = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + payload


def strip_comments(markdown: str) -> str:
    return re.sub(r"<!--.*?-->", "", markdown, flags=re.DOTALL)


def clean_inline(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def plain_inline(text: str) -> str:
    value = clean_inline(text)
    value = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", value)
    value = re.sub(r"(\*\*|__|\*|_|\x60)", "", value)
    return value.strip()


def is_chinese_language(language: str) -> bool:
    return language.lower().startswith("zh")


def metadata_value(metadata: dict[str, Any], *keys: str) -> str:
    value: Any = metadata
    for key in keys:
        if not isinstance(value, dict):
            return ""
        value = value.get(key)
    return str(value).strip() if value is not None else ""


def presentation_labels(
    language: str,
    title: str,
    metadata: dict[str, Any],
) -> dict[str, str]:
    custom = metadata.get("docxLabels")
    custom = custom if isinstance(custom, dict) else {}
    keyword = metadata_value(metadata, "keyword")
    office_terms = re.compile(
        r"conference|boardroom|meeting|office|workplace|\u4f1a\u8bae|\u8463\u4e8b\u4f1a|\u529e\u516c",
        flags=re.IGNORECASE,
    )
    office_guide = bool(office_terms.search(f"{title} {keyword}"))
    if is_chinese_language(language):
        defaults = {
            "header": "SHOPIFY BLOG \u8349\u7a3f  |  \u529e\u516c\u7a7a\u95f4\u89c4\u5212\u6307\u5357"
            if office_guide
            else "SHOPIFY BLOG \u8349\u7a3f  |  \u91c7\u8d2d\u4e0e\u89c4\u5212\u6307\u5357",
            "footer": "\u672c\u5730\u9884\u89c8 - \u672a\u53d1\u5e03  |  ",
            "eyebrow": "\u5546\u4e1a\u529e\u516c\u91c7\u8d2d\u4e0e\u89c4\u5212\u6307\u5357"
            if office_guide
            else "\u4ea7\u54c1\u91c7\u8d2d\u4e0e\u89c4\u5212\u6307\u5357",
            "subtitle": "\u672c\u5730\u7f16\u8f91\u9884\u89c8\u3002\u672a\u53d1\u5e03\u5230 Shopify\u3002",
            "field": "\u5b57\u6bb5",
            "value": "\u5185\u5bb9",
            "keyword": "\u4e3b\u8981\u5173\u952e\u8bcd",
            "seo_title": "SEO \u6807\u9898",
            "url_handle": "URL \u8def\u5f84",
            "search_intent": "\u641c\u7d22\u610f\u56fe",
            "image_pending": "\u56fe\u7247\u5f85\u8865",
        }
    else:
        defaults = {
            "header": "SHOPIFY BLOG DRAFT  |  OFFICE PLANNING GUIDE"
            if office_guide
            else "SHOPIFY BLOG DRAFT  |  BUYING & PLANNING GUIDE",
            "footer": "Local preview - not published  |  ",
            "eyebrow": "COMMERCIAL OFFICE BUYING GUIDE"
            if office_guide
            else "PRODUCT BUYING & PLANNING GUIDE",
            "subtitle": "Local editorial preview. Not published to Shopify.",
            "field": "Field",
            "value": "Value",
            "keyword": "Primary keyword",
            "seo_title": "SEO title",
            "url_handle": "URL handle",
            "search_intent": "Search intent",
            "image_pending": "Image pending",
        }
    for key in defaults:
        replacement = custom.get(key)
        if isinstance(replacement, str) and replacement.strip():
            defaults[key] = replacement.strip()
    return defaults


def placeholder_png(width: int = 1200, height: int = 500) -> bytes:
    """Create a neutral 1200:500 PNG without third-party imaging libraries."""

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
        )

    border = bytes((190, 190, 190))
    fill = bytes((242, 242, 242))
    rows = []
    for y in range(height):
        if y in (0, height - 1):
            row = border * width
        else:
            row = border + fill * (width - 2) + border
        rows.append(b"\x00" + row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(b"".join(rows), level=9))
        + chunk(b"IEND", b"")
    )


class DocumentBuilder:
    def __init__(
        self,
        language: str,
        metadata: dict[str, Any],
        source_dir: Path,
        allow_placeholders: bool = False,
    ) -> None:
        self.language = language
        self.metadata = metadata
        self.source_dir = source_dir
        self.allow_placeholders = allow_placeholders
        self.root = ET.Element(w("document"))
        self.body = add(self.root, "body")
        self.relationships: list[tuple[str, str, str, str | None]] = [
            (
                "rId1",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
                "styles.xml",
                None,
            ),
            (
                "rId2",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering",
                "numbering.xml",
                None,
            ),
            (
                "rId3",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings",
                "settings.xml",
                None,
            ),
            (
                "rId4",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header",
                "header1.xml",
                None,
            ),
            (
                "rId5",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer",
                "footer1.xml",
                None,
            ),
        ]
        self.next_relationship = 10
        self.media: list[tuple[str, bytes]] = []
        self.next_drawing_id = 1
        self.title = "SEO Blog Draft"
        self.front_matter_added = False
        self.labels = presentation_labels(language, self.title, metadata)

    def relationship(self, target: str, relationship_type: str, external: bool = False) -> str:
        relationship_id = f"rId{self.next_relationship}"
        self.next_relationship += 1
        self.relationships.append(
            (relationship_id, relationship_type, target, "External" if external else None)
        )
        return relationship_id

    def paragraph(
        self,
        style: str | None = None,
        *,
        parent: ET.Element | None = None,
    ) -> tuple[ET.Element, ET.Element]:
        paragraph = add(parent if parent is not None else self.body, "p")
        properties = add(paragraph, "pPr")
        if style:
            add(properties, "pStyle", {"val": style})
        return paragraph, properties

    def run(
        self,
        parent: ET.Element,
        text: str,
        *,
        bold: bool = False,
        italic: bool = False,
        code: bool = False,
        style: str | None = None,
    ) -> ET.Element:
        run = add(parent, "r")
        properties = add(run, "rPr")
        if style:
            add(properties, "rStyle", {"val": style})
        if bold:
            add(properties, "b")
        if italic:
            add(properties, "i")
        if code:
            add(
                properties,
                "rFonts",
                {
                    "ascii": "Courier New",
                    "hAnsi": "Courier New",
                    "eastAsia": CJK_FONT,
                },
            )
            add(properties, "shd", {"val": "clear", "color": "auto", "fill": "F2F2F2"})
        text_node = add(run, "t")
        if text[:1].isspace() or text[-1:].isspace():
            text_node.set(q(XML, "space"), "preserve")
        text_node.text = text
        return run

    def inline(self, parent: ET.Element, value: str, *, bold: bool = False) -> None:
        value = clean_inline(value)
        token_pattern = re.compile(
            r"\[([^\]]+)\]\(([^\)]+)\)"
            r"|\*\*([^*]+)\*\*"
            r"|(?<!\*)\*([^*]+)\*(?!\*)"
            r"|\x60([^\x60]+)\x60"
        )
        cursor = 0
        for match in token_pattern.finditer(value):
            if match.start() > cursor:
                self.run(parent, value[cursor : match.start()], bold=bold)
            link_text, url, strong, emphasis, code = match.groups()
            if link_text is not None and url is not None:
                link_bold = bold
                link_italic = False
                if link_text.startswith("**") and link_text.endswith("**"):
                    link_text = link_text[2:-2]
                    link_bold = True
                elif link_text.startswith("*") and link_text.endswith("*"):
                    link_text = link_text[1:-1]
                    link_italic = True
                relationship_id = self.relationship(
                    url.strip(),
                    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                    external=True,
                )
                hyperlink = add(parent, "hyperlink")
                hyperlink.set(q(R, "id"), relationship_id)
                self.run(
                    hyperlink,
                    link_text,
                    bold=link_bold,
                    italic=link_italic,
                    style="Hyperlink",
                )
            elif strong is not None:
                self.run(parent, strong, bold=True)
            elif emphasis is not None:
                self.run(parent, emphasis, bold=bold, italic=True)
            elif code is not None:
                self.run(parent, code, bold=bold, code=True)
            cursor = match.end()
        if cursor < len(value):
            self.run(parent, value[cursor:], bold=bold)

    def add_front_matter(self, title: str) -> None:
        self.title = plain_inline(title) or "SEO Blog Draft"
        self.labels = presentation_labels(self.language, self.title, self.metadata)

        eyebrow, _ = self.paragraph("Eyebrow")
        self.run(eyebrow, self.labels["eyebrow"])

        title_paragraph, _ = self.paragraph("Title")
        self.run(title_paragraph, self.title, bold=True)

        subtitle, _ = self.paragraph("Subtitle")
        self.run(subtitle, self.labels["subtitle"], italic=True)

        self.add_metadata_table()
        self.front_matter_added = True

    def add_metadata_table(self) -> None:
        seo_title = metadata_value(self.metadata, "seo", "seoTitle") or self.title
        keyword = metadata_value(self.metadata, "keyword") or self.title
        url_handle = metadata_value(self.metadata, "seo", "urlHandle") or "not-supplied"
        search_intent = metadata_value(self.metadata, "searchIntent") or "commercial investigation"
        rows = [
            [self.labels["field"], self.labels["value"]],
            [self.labels["keyword"], keyword],
            [self.labels["seo_title"], seo_title],
            [self.labels["url_handle"], url_handle],
            [self.labels["search_intent"], search_intent],
        ]
        self._add_table(rows, [1900, 7460], metadata_table=True)

    def add_heading(self, level: int, text: str) -> None:
        if level == 1:
            if not self.front_matter_added:
                self.add_front_matter(text)
            return
        style = f"Heading{min(max(level - 1, 1), 3)}"
        paragraph, _ = self.paragraph(style)
        self.inline(paragraph, text)

    def add_body_paragraph(self, text: str) -> None:
        paragraph, _ = self.paragraph("Normal")
        self.inline(paragraph, text)

    def add_list_item(self, text: str, ordered: bool, level: int) -> None:
        paragraph, properties = self.paragraph("ListParagraph")
        numbering = add(properties, "numPr")
        add(numbering, "ilvl", {"val": str(min(level, 2))})
        add(numbering, "numId", {"val": "2" if ordered else "1"})
        self.inline(paragraph, text)

    def add_quote(self, text: str) -> None:
        paragraph, properties = self.paragraph("Quote")
        borders = add(properties, "pBdr")
        add(borders, "left", {"val": "single", "sz": "12", "space": "10", "color": "7F7F7F"})
        self.inline(paragraph, text)

    def _image_payload(self, source: str) -> tuple[bytes, str, bool]:
        candidate = source.strip()
        bracketed_path = candidate.startswith("<") and candidate.endswith(">")
        if bracketed_path:
            candidate = candidate[1:-1]
        else:
            candidate = candidate.split(maxsplit=1)[0]
        candidate = unquote(candidate)
        path = Path(candidate)
        if not path.is_absolute():
            path = self.source_dir / path
        try:
            payload = path.read_bytes()
        except OSError as exc:
            if self.allow_placeholders:
                return placeholder_png(), "png", True
            raise ValueError(f"image is missing or unreadable: {path}") from exc
        if payload.startswith(b"\x89PNG\r\n\x1a\n"):
            return payload, "png", False
        if payload.startswith(b"\xff\xd8"):
            return payload, "jpg", False
        if self.allow_placeholders:
            return placeholder_png(), "png", True
        raise ValueError(f"image must be a valid PNG or JPEG file: {path}")

    def _drawing(self, relationship_id: str, filename: str, alt_text: str) -> ET.Element:
        drawing_id = self.next_drawing_id
        self.next_drawing_id += 1

        drawing = ET.Element(w("drawing"))
        inline = ns_add(
            drawing,
            WP,
            "inline",
            {"distT": "0", "distB": "0", "distL": "0", "distR": "0"},
        )
        ns_add(
            inline,
            WP,
            "extent",
            {"cx": str(IMAGE_WIDTH_EMU), "cy": str(IMAGE_HEIGHT_EMU)},
        )
        ns_add(
            inline,
            WP,
            "effectExtent",
            {"l": "0", "t": "0", "r": "0", "b": "0"},
        )
        ns_add(
            inline,
            WP,
            "docPr",
            {
                "id": str(drawing_id),
                "name": f"Blog image {drawing_id}",
                "descr": alt_text,
            },
        )
        frame_properties = ns_add(inline, WP, "cNvGraphicFramePr")
        ns_add(frame_properties, A, "graphicFrameLocks", {"noChangeAspect": "1"})

        graphic = ns_add(inline, A, "graphic")
        graphic_data = ns_add(
            graphic,
            A,
            "graphicData",
            {"uri": "http://schemas.openxmlformats.org/drawingml/2006/picture"},
        )
        picture = ns_add(graphic_data, PIC, "pic")
        nonvisual = ns_add(picture, PIC, "nvPicPr")
        ns_add(
            nonvisual,
            PIC,
            "cNvPr",
            {"id": "0", "name": filename, "descr": alt_text},
        )
        ns_add(nonvisual, PIC, "cNvPicPr")

        blip_fill = ns_add(picture, PIC, "blipFill")
        blip = ns_add(blip_fill, A, "blip")
        blip.set(q(R, "embed"), relationship_id)
        stretch = ns_add(blip_fill, A, "stretch")
        ns_add(stretch, A, "fillRect")

        shape_properties = ns_add(picture, PIC, "spPr")
        transform = ns_add(shape_properties, A, "xfrm")
        ns_add(transform, A, "off", {"x": "0", "y": "0"})
        ns_add(
            transform,
            A,
            "ext",
            {"cx": str(IMAGE_WIDTH_EMU), "cy": str(IMAGE_HEIGHT_EMU)},
        )
        geometry = ns_add(shape_properties, A, "prstGeom", {"prst": "rect"})
        ns_add(geometry, A, "avLst")
        return drawing

    def add_image(self, alt_text: str, source: str) -> None:
        safe_alt = plain_inline(alt_text) or Path(source).name or "Blog image"
        payload, extension, missing = self._image_payload(source)
        filename = f"image{len(self.media) + 1}.{extension}"
        self.media.append((filename, payload))
        relationship_id = self.relationship(
            f"media/{filename}",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
        )

        paragraph, _ = self.paragraph("Image")
        run = add(paragraph, "r")
        add(run, "rPr")
        run.append(self._drawing(relationship_id, filename, safe_alt))

        caption_text = (
            f"{self.labels['image_pending']}: {safe_alt}" if missing else safe_alt
        )
        caption, _ = self.paragraph("Caption")
        self.run(caption, caption_text, italic=True)

    @staticmethod
    def _column_widths(column_count: int) -> list[int]:
        if column_count == 4:
            return [1550, 2050, 2250, 3510]
        base = TABLE_WIDTH_DXA // column_count
        widths = [base] * column_count
        widths[-1] += TABLE_WIDTH_DXA - sum(widths)
        return widths

    def _add_table(
        self,
        rows: list[list[str]],
        widths: list[int],
        *,
        metadata_table: bool = False,
    ) -> None:
        table = add(self.body, "tbl")
        properties = add(table, "tblPr")
        add(properties, "tblW", {"w": str(TABLE_WIDTH_DXA), "type": "dxa"})
        add(properties, "jc", {"val": "left"})
        add(properties, "tblLayout", {"type": "fixed"})
        add(
            properties,
            "tblLook",
            {
                "val": "04A0",
                "firstRow": "1",
                "lastRow": "0",
                "firstColumn": "1" if metadata_table else "0",
                "lastColumn": "0",
                "noHBand": "0",
                "noVBand": "1",
            },
        )
        borders = add(properties, "tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            add(borders, side, {"val": "single", "sz": "4", "space": "0", "color": "B7B7B7"})
        margins = add(properties, "tblCellMar")
        for side, width in (("top", "80"), ("left", "100"), ("bottom", "80"), ("right", "100")):
            add(margins, side, {"w": width, "type": "dxa"})
        grid = add(table, "tblGrid")
        for width in widths:
            add(grid, "gridCol", {"w": str(width)})

        for row_index, row_values in enumerate(rows):
            row = add(table, "tr")
            row_properties = add(row, "trPr")
            add(row_properties, "cantSplit")
            if row_index == 0:
                add(row_properties, "tblHeader")
            for column_index, width in enumerate(widths):
                cell = add(row, "tc")
                cell_properties = add(cell, "tcPr")
                add(cell_properties, "tcW", {"w": str(width), "type": "dxa"})
                shaded = row_index == 0 or (metadata_table and column_index == 0)
                if shaded:
                    add(cell_properties, "shd", {"val": "clear", "color": "auto", "fill": "F2F2F2"})
                paragraph, _ = self.paragraph(
                    "MetaTableText" if metadata_table else "TableText",
                    parent=cell,
                )
                value = row_values[column_index].strip() if column_index < len(row_values) else ""
                self.inline(
                    paragraph,
                    value,
                    bold=row_index == 0 or (metadata_table and column_index == 0),
                )

    def add_table(self, rows: list[list[str]]) -> None:
        if not rows:
            return
        column_count = max(len(row) for row in rows)
        self._add_table(rows, self._column_widths(column_count))

    def add_rule(self) -> None:
        paragraph, properties = self.paragraph("Normal")
        borders = add(properties, "pBdr")
        add(borders, "bottom", {"val": "single", "sz": "4", "space": "8", "color": "B7B7B7"})
        self.run(paragraph, "")

    def finish(self) -> None:
        section = add(self.body, "sectPr")
        header_reference = add(section, "headerReference", {"type": "default"})
        header_reference.set(q(R, "id"), "rId4")
        footer_reference = add(section, "footerReference", {"type": "default"})
        footer_reference.set(q(R, "id"), "rId5")
        add(
            section,
            "pgSz",
            {"w": str(LETTER_WIDTH_DXA), "h": str(LETTER_HEIGHT_DXA)},
        )
        add(
            section,
            "pgMar",
            {
                "top": str(ONE_INCH_DXA),
                "right": str(ONE_INCH_DXA),
                "bottom": str(ONE_INCH_DXA),
                "left": str(ONE_INCH_DXA),
                "header": "720",
                "footer": "720",
                "gutter": "0",
            },
        )
        add(section, "cols", {"space": "720"})
        add(section, "docGrid", {"linePitch": "360"})


def join_paragraph_lines(lines: list[str]) -> str:
    if not lines:
        return ""
    result = lines[0].strip()
    cjk = re.compile(r"[\u3400-\u9fff]")
    for line in lines[1:]:
        value = line.strip()
        if result and value and cjk.fullmatch(result[-1]) and cjk.fullmatch(value[0]):
            result += value
        else:
            result += " " + value
    return result


def parse_table_row(line: str) -> list[str]:
    value = line.strip().strip("|")
    return [part.replace("\\|", "|").strip() for part in re.split(r"(?<!\\)\|", value)]


def is_table_separator(line: str) -> bool:
    cells = parse_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def populate(builder: DocumentBuilder, markdown: str) -> None:
    lines = strip_comments(markdown).splitlines()
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            builder.add_body_paragraph(join_paragraph_lines(paragraph_lines))
            paragraph_lines.clear()

    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue

        table_candidate = (
            stripped.startswith("|")
            and index + 1 < len(lines)
            and is_table_separator(lines[index + 1])
        )
        if table_candidate:
            flush_paragraph()
            rows = [parse_table_row(line)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(parse_table_row(lines[index]))
                index += 1
            builder.add_table(rows)
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        image = re.match(r"^!\[([^\]]*)\]\((.+)\)$", stripped)
        list_item = re.match(r"^(\s*)([-+*]|\d+\.)\s+(.+)$", line)
        if heading:
            flush_paragraph()
            builder.add_heading(len(heading.group(1)), heading.group(2))
        elif image:
            flush_paragraph()
            builder.add_image(image.group(1), image.group(2))
        elif list_item:
            flush_paragraph()
            marker = list_item.group(2)
            builder.add_list_item(
                list_item.group(3),
                ordered=marker[0].isdigit(),
                level=len(list_item.group(1).replace("\t", "    ")) // 2,
            )
        elif stripped.startswith(">"):
            flush_paragraph()
            builder.add_quote(stripped.lstrip("> "))
        elif re.fullmatch(r"(?:-{3,}|\*{3,}|_{3,})", stripped):
            flush_paragraph()
            builder.add_rule()
        else:
            paragraph_lines.append(stripped)
        index += 1
    flush_paragraph()


def styles_xml(language: str) -> bytes:
    styles = ET.Element(w("styles"))
    defaults = add(styles, "docDefaults")
    run_default = add(add(defaults, "rPrDefault"), "rPr")
    add(
        run_default,
        "rFonts",
        {
            "ascii": "Calibri",
            "hAnsi": "Calibri",
            "eastAsia": CJK_FONT,
            "cs": "Calibri",
        },
    )
    add(run_default, "lang", {"val": language, "eastAsia": "zh-CN"})
    add(run_default, "sz", {"val": "22"})
    add(run_default, "szCs", {"val": "22"})
    paragraph_default = add(add(defaults, "pPrDefault"), "pPr")
    add(paragraph_default, "spacing", {"after": "120", "line": "264", "lineRule": "auto"})

    def paragraph_style(
        style_id: str,
        name: str,
        *,
        based_on: str | None = "Normal",
        size: str | None = None,
        bold: bool = False,
        italic: bool = False,
        before: str | None = None,
        after: str | None = None,
        line: str | None = None,
        keep_next: bool = False,
        keep_lines: bool = False,
        outline: str | None = None,
        alignment: str | None = None,
    ) -> ET.Element:
        style = add(styles, "style", {"type": "paragraph", "styleId": style_id})
        add(style, "name", {"val": name})
        if based_on:
            add(style, "basedOn", {"val": based_on})
        add(style, "qFormat")
        properties = add(style, "pPr")
        spacing_attrs: dict[str, str] = {}
        if before is not None:
            spacing_attrs["before"] = before
        if after is not None:
            spacing_attrs["after"] = after
        if line is not None:
            spacing_attrs["line"] = line
            spacing_attrs["lineRule"] = "auto"
        if spacing_attrs:
            add(properties, "spacing", spacing_attrs)
        if keep_next:
            add(properties, "keepNext")
        if keep_lines:
            add(properties, "keepLines")
        if outline is not None:
            add(properties, "outlineLvl", {"val": outline})
        if alignment is not None:
            add(properties, "jc", {"val": alignment})
        run_properties = add(style, "rPr")
        add(
            run_properties,
            "rFonts",
            {
                "ascii": "Calibri",
                "hAnsi": "Calibri",
                "eastAsia": CJK_FONT,
                "cs": "Calibri",
            },
        )
        add(run_properties, "color", {"val": "000000"})
        if size:
            add(run_properties, "sz", {"val": size})
            add(run_properties, "szCs", {"val": size})
        if bold:
            add(run_properties, "b")
        if italic:
            add(run_properties, "i")
        return style

    normal = add(styles, "style", {"type": "paragraph", "default": "1", "styleId": "Normal"})
    add(normal, "name", {"val": "Normal"})
    add(normal, "qFormat")
    normal_ppr = add(normal, "pPr")
    add(normal_ppr, "spacing", {"after": "120", "line": "264", "lineRule": "auto"})
    normal_rpr = add(normal, "rPr")
    add(
        normal_rpr,
        "rFonts",
        {
            "ascii": "Calibri",
            "hAnsi": "Calibri",
            "eastAsia": CJK_FONT,
            "cs": "Calibri",
        },
    )
    add(normal_rpr, "color", {"val": "000000"})
    add(normal_rpr, "sz", {"val": "22"})
    add(normal_rpr, "szCs", {"val": "22"})

    paragraph_style("Eyebrow", "Eyebrow", size="19", bold=True, after="100", keep_next=True)
    paragraph_style("Title", "Title", size="48", bold=True, after="160", keep_next=True, outline="0")
    paragraph_style("Subtitle", "Subtitle", size="20", italic=True, after="280", keep_next=True)
    paragraph_style(
        "Heading1",
        "Heading 1",
        size="32",
        bold=True,
        before="320",
        after="160",
        keep_next=True,
        outline="0",
    )
    paragraph_style(
        "Heading2",
        "Heading 2",
        size="26",
        bold=True,
        before="240",
        after="120",
        keep_next=True,
        outline="1",
    )
    paragraph_style(
        "Heading3",
        "Heading 3",
        size="24",
        bold=True,
        before="160",
        after="80",
        keep_next=True,
        outline="2",
    )
    paragraph_style("Quote", "Quote", size="22", italic=True, before="80", after="120")
    list_style = paragraph_style("ListParagraph", "List Paragraph", size="22", after="80", line="264")
    list_ppr = list_style.find(w("pPr"))
    assert list_ppr is not None
    add(list_ppr, "ind", {"left": "720", "hanging": "360"})
    paragraph_style(
        "Image",
        "Image",
        before="120",
        after="0",
        keep_next=True,
        keep_lines=True,
        alignment="center",
    )
    paragraph_style(
        "Caption",
        "Caption",
        size="18",
        italic=True,
        after="160",
        keep_lines=True,
        alignment="center",
    )
    paragraph_style("MetaTableText", "Metadata Table Text", size="18", after="40", line="220")
    paragraph_style("TableText", "Table Text", size="17", after="40", line="220")

    hyperlink = add(styles, "style", {"type": "character", "styleId": "Hyperlink"})
    add(hyperlink, "name", {"val": "Hyperlink"})
    hyperlink_rpr = add(hyperlink, "rPr")
    add(
        hyperlink_rpr,
        "rFonts",
        {
            "ascii": "Calibri",
            "hAnsi": "Calibri",
            "eastAsia": CJK_FONT,
            "cs": "Calibri",
        },
    )
    add(hyperlink_rpr, "color", {"val": "000000"})
    add(hyperlink_rpr, "u", {"val": "single"})
    return xml_bytes(styles)


def numbering_xml() -> bytes:
    numbering = ET.Element(w("numbering"))

    def abstract(number_id: int, ordered: bool) -> None:
        abstract_num = add(numbering, "abstractNum", {"abstractNumId": str(number_id)})
        add(abstract_num, "multiLevelType", {"val": "multilevel"})
        for level in range(3):
            lvl = add(abstract_num, "lvl", {"ilvl": str(level)})
            add(lvl, "start", {"val": "1"})
            add(lvl, "numFmt", {"val": "decimal" if ordered else "bullet"})
            bullet = "\u2022" if level % 2 == 0 else "\u2013"
            add(lvl, "lvlText", {"val": f"%{level + 1}." if ordered else bullet})
            add(lvl, "lvlJc", {"val": "left"})
            paragraph_properties = add(lvl, "pPr")
            add(
                paragraph_properties,
                "ind",
                {"left": str(720 + level * 360), "hanging": "360"},
            )
            if not ordered:
                run_properties = add(lvl, "rPr")
                add(run_properties, "rFonts", {"ascii": "Arial", "hAnsi": "Arial"})

    abstract(0, ordered=False)
    abstract(1, ordered=True)
    for number_id, abstract_id in ((1, 0), (2, 1)):
        num = add(numbering, "num", {"numId": str(number_id)})
        add(num, "abstractNumId", {"val": str(abstract_id)})
    return xml_bytes(numbering)


def relationships_xml(relationships: list[tuple[str, str, str, str | None]]) -> bytes:
    root = ET.Element("Relationships", {"xmlns": REL})
    for relationship_id, relationship_type, target, target_mode in relationships:
        attrs = {"Id": relationship_id, "Type": relationship_type, "Target": target}
        if target_mode:
            attrs["TargetMode"] = target_mode
        ET.SubElement(root, "Relationship", attrs)
    return xml_bytes(root)


def _header_footer_run_properties(parent: ET.Element, *, bold: bool = False) -> ET.Element:
    properties = add(parent, "rPr")
    add(
        properties,
        "rFonts",
        {
            "ascii": "Calibri",
            "hAnsi": "Calibri",
            "eastAsia": CJK_FONT,
            "cs": "Calibri",
        },
    )
    add(properties, "color", {"val": "000000"})
    add(properties, "sz", {"val": "17"})
    add(properties, "szCs", {"val": "17"})
    if bold:
        add(properties, "b")
    return properties


def header_xml(text: str) -> bytes:
    header = ET.Element(w("hdr"))
    paragraph = add(header, "p")
    properties = add(paragraph, "pPr")
    add(properties, "jc", {"val": "left"})
    run = add(paragraph, "r")
    _header_footer_run_properties(run, bold=True)
    text_node = add(run, "t")
    text_node.text = text
    return xml_bytes(header)


def footer_xml(text: str) -> bytes:
    footer = ET.Element(w("ftr"))
    paragraph = add(footer, "p")
    properties = add(paragraph, "pPr")
    add(properties, "jc", {"val": "right"})

    prefix_run = add(paragraph, "r")
    _header_footer_run_properties(prefix_run)
    prefix_text = add(prefix_run, "t")
    prefix_text.set(q(XML, "space"), "preserve")
    prefix_text.text = text

    begin_run = add(paragraph, "r")
    _header_footer_run_properties(begin_run)
    add(begin_run, "fldChar", {"fldCharType": "begin"})
    instruction_run = add(paragraph, "r")
    _header_footer_run_properties(instruction_run)
    instruction = add(instruction_run, "instrText")
    instruction.set(q(XML, "space"), "preserve")
    instruction.text = " PAGE "
    separate_run = add(paragraph, "r")
    _header_footer_run_properties(separate_run)
    add(separate_run, "fldChar", {"fldCharType": "separate"})
    display_run = add(paragraph, "r")
    _header_footer_run_properties(display_run)
    display_text = add(display_run, "t")
    display_text.text = "1"
    end_run = add(paragraph, "r")
    _header_footer_run_properties(end_run)
    add(end_run, "fldChar", {"fldCharType": "end"})
    return xml_bytes(footer)


def content_types_xml() -> bytes:
    root = ET.Element("Types", {"xmlns": CT})
    defaults = {
        "rels": "application/vnd.openxmlformats-package.relationships+xml",
        "xml": "application/xml",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    for extension, content_type in defaults.items():
        ET.SubElement(
            root,
            "Default",
            {"Extension": extension, "ContentType": content_type},
        )
    overrides = {
        "/word/document.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
        "/word/styles.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
        "/word/numbering.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml",
        "/word/settings.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml",
        "/word/header1.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml",
        "/word/footer1.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
        "/docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
        "/docProps/app.xml": "application/vnd.openxmlformats-officedocument.extended-properties+xml",
    }
    for part_name, content_type in overrides.items():
        ET.SubElement(
            root,
            "Override",
            {"PartName": part_name, "ContentType": content_type},
        )
    return xml_bytes(root)


def package_relationships_xml() -> bytes:
    relationships = [
        (
            "rId1",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "word/document.xml",
            None,
        ),
        (
            "rId2",
            "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
            "docProps/core.xml",
            None,
        ),
        (
            "rId3",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
            "docProps/app.xml",
            None,
        ),
    ]
    return relationships_xml(relationships)


def settings_xml() -> bytes:
    settings = ET.Element(w("settings"))
    add(settings, "zoom", {"percent": "100"})
    add(settings, "defaultTabStop", {"val": "720"})
    add(settings, "updateFields", {"val": "true"})
    return xml_bytes(settings)


def core_properties_xml(title: str, language: str) -> bytes:
    root = ET.Element(q(CP, "coreProperties"))
    ET.SubElement(root, q(DC, "title")).text = title
    ET.SubElement(root, q(DC, "creator")).text = "Shopify SEO Blog Writer Skill"
    ET.SubElement(root, q(CP, "lastModifiedBy")).text = "Shopify SEO Blog Writer Skill"
    ET.SubElement(root, q(DC, "language")).text = language
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    created = ET.SubElement(root, q(DCTERMS, "created"), {q(XSI, "type"): "dcterms:W3CDTF"})
    created.text = timestamp
    modified = ET.SubElement(root, q(DCTERMS, "modified"), {q(XSI, "type"): "dcterms:W3CDTF"})
    modified.text = timestamp
    return xml_bytes(root)


def app_properties_xml() -> bytes:
    root = ET.Element(q(EP, "Properties"))
    ET.SubElement(root, q(EP, "Application")).text = "Shopify SEO Blog Writer Skill"
    ET.SubElement(root, q(EP, "AppVersion")).text = "1.2"
    ET.SubElement(root, q(EP, "DocSecurity")).text = "0"
    ET.SubElement(root, q(EP, "ScaleCrop")).text = "false"
    return xml_bytes(root)


def extract_markdown_title(markdown: str) -> str:
    match = re.search(r"^#\s+(.+)$", strip_comments(markdown), flags=re.MULTILINE)
    return plain_inline(match.group(1)) if match else ""


def default_metadata(title: str, stem: str = "seo-blog-draft") -> dict[str, Any]:
    handle = re.sub(r"\.(?:zh-CN|en)$", "", stem, flags=re.IGNORECASE)
    handle = re.sub(r"-v\d+$", "", handle)
    handle = re.sub(r"[^a-z0-9]+", "-", handle.lower()).strip("-") or "seo-blog-draft"
    return {
        "keyword": title,
        "searchIntent": "commercial investigation",
        "seo": {
            "seoTitle": title,
            "urlHandle": handle,
        },
    }


def infer_metadata_path(input_path: Path) -> Path:
    name = input_path.name
    if name.endswith(".zh-CN.md"):
        stem = name[: -len(".zh-CN.md")]
    elif name.endswith(".en.md"):
        stem = name[: -len(".en.md")]
    elif name.endswith(".md"):
        stem = name[: -len(".md")]
    else:
        stem = input_path.stem
    return input_path.parent / f"{stem}.meta.json"


def load_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    value = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"metadata must be a JSON object: {path}")
    return value


def build_docx(
    markdown: str,
    output: Path,
    language: str = "en-US",
    title: str | None = None,
    *,
    source_dir: Path | None = None,
    metadata: dict[str, Any] | None = None,
    source_stem: str = "seo-blog-draft",
    allow_placeholders: bool = False,
) -> Path:
    output = output.expanduser().resolve()
    if output.suffix.lower() != ".docx":
        raise ValueError("output file must use the .docx extension")
    output.parent.mkdir(parents=True, exist_ok=True)

    document_title = title or extract_markdown_title(markdown) or "SEO Blog Draft"
    resolved_metadata = metadata or default_metadata(document_title, source_stem)
    builder = DocumentBuilder(
        language,
        resolved_metadata,
        (source_dir or output.parent).expanduser().resolve(),
        allow_placeholders,
    )
    builder.add_front_matter(document_title)
    populate(builder, markdown)
    builder.finish()

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml())
        archive.writestr("_rels/.rels", package_relationships_xml())
        archive.writestr("docProps/core.xml", core_properties_xml(builder.title, language))
        archive.writestr("docProps/app.xml", app_properties_xml())
        archive.writestr("word/document.xml", xml_bytes(builder.root))
        archive.writestr("word/styles.xml", styles_xml(language))
        archive.writestr("word/numbering.xml", numbering_xml())
        archive.writestr("word/settings.xml", settings_xml())
        archive.writestr("word/header1.xml", header_xml(builder.labels["header"]))
        archive.writestr("word/footer1.xml", footer_xml(builder.labels["footer"]))
        archive.writestr("word/_rels/document.xml.rels", relationships_xml(builder.relationships))
        for filename, payload in builder.media:
            archive.writestr(f"word/media/{filename}", payload)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 Markdown source")
    parser.add_argument("--output", required=True, type=Path, help="Destination .docx file")
    parser.add_argument("--language", default="en-US", help="BCP 47 language tag, such as en-US or zh-CN")
    parser.add_argument("--title", help="Optional document-property title override")
    parser.add_argument(
        "--meta",
        type=Path,
        help="Metadata JSON; defaults to the matching <slug>.meta.json when present",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow neutral placeholder images for debugging only; final bundle validation rejects them",
    )
    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    markdown = input_path.read_text(encoding="utf-8")
    metadata_path = args.meta.expanduser().resolve() if args.meta else infer_metadata_path(input_path)
    if args.meta and not metadata_path.is_file():
        parser.error(f"metadata file not found: {metadata_path}")
    metadata = load_metadata(metadata_path) if metadata_path.is_file() else {}
    try:
        destination = build_docx(
            markdown,
            args.output,
            args.language,
            args.title,
            source_dir=input_path.parent,
            metadata=metadata or None,
            source_stem=input_path.stem,
            allow_placeholders=args.allow_placeholders,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Created {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
