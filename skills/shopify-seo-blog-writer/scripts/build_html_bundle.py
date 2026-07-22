#!/usr/bin/env python3
"""Build English, Chinese, and bilingual local HTML previews from Markdown."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def inline(text: str) -> str:
    placeholders: list[str] = []

    def stash(value: str) -> str:
        placeholders.append(value)
        return f"\x00{len(placeholders) - 1}\x00"

    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda m: stash(
            f'<a href="{html.escape(m.group(2), quote=True)}" target="_blank" rel="noopener">'
            f"{html.escape(m.group(1))}</a>"
        ),
        text,
    )
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    for index, value in enumerate(placeholders):
        text = text.replace(f"\x00{index}\x00", value)
    return text


def markdown_body(source: str) -> str:
    lines = source.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            output.append(f"</{list_type}>")
            list_type = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            close_list()
            continue
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            flush_paragraph()
            close_list()
            output.append(stripped)
            continue
        image_match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            close_list()
            alt, src = image_match.groups()
            output.append(
                f'<figure><img src="{html.escape(src, quote=True)}" '
                f'alt="{html.escape(alt, quote=True)}" width="1200" height="500" loading="lazy"></figure>'
            )
            continue
        heading = re.fullmatch(r"(#{1,3})\s+(.+)", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            output.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            continue
        unordered = re.fullmatch(r"[-*]\s+(.+)", stripped)
        ordered = re.fullmatch(r"\d+\.\s+(.+)", stripped)
        if unordered or ordered:
            flush_paragraph()
            wanted = "ul" if unordered else "ol"
            if list_type != wanted:
                close_list()
                output.append(f"<{wanted}>")
                list_type = wanted
            output.append(f"<li>{inline((unordered or ordered).group(1))}</li>")
            continue
        close_list()
        paragraph.append(stripped)

    flush_paragraph()
    close_list()
    return "\n".join(output)


STYLE = """
body{margin:0;background:#f5f3ef;color:#171717;font:17px/1.7 Arial,sans-serif}
main{max-width:940px;margin:0 auto;background:#fff;padding:48px 64px 80px}
h1{font-size:42px;line-height:1.15;margin:0 0 28px}h2{font-size:28px;margin:48px 0 14px}
h3{font-size:21px;margin:28px 0 8px}p{margin:0 0 18px}li{margin:7px 0}
figure{margin:28px 0}img{display:block;width:100%;height:auto;border-radius:2px}
a{color:#174b6b}.notice{font-size:14px;color:#666}.bilingual{max-width:1480px}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:36px}.column{min-width:0}
@media(max-width:900px){main{padding:30px 22px}.columns{grid-template-columns:1fr}h1{font-size:34px}}
"""


def document(title: str, body: str, language: str, bilingual: bool = False) -> str:
    klass = ' class="bilingual"' if bilingual else ""
    return (
        "<!doctype html>\n"
        f'<html lang="{language}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{STYLE}</style></head><body>"
        f"<main{klass}>{body}</main></body></html>\n"
    )


def h1_title(markdown: str) -> str:
    match = re.search(r"^# (.+)$", markdown, flags=re.MULTILINE)
    return match.group(1) if match else "Blog preview"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--english", type=Path, required=True)
    parser.add_argument("--chinese", type=Path, required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    en_source = args.english.read_text(encoding="utf-8")
    zh_source = args.chinese.read_text(encoding="utf-8")
    en_body = markdown_body(en_source)
    zh_body = markdown_body(zh_source)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    (args.output_dir / f"{args.slug}.html").write_text(
        document(h1_title(en_source), en_body, "en-US"), encoding="utf-8"
    )
    (args.output_dir / f"{args.slug}.zh-CN.html").write_text(
        document(h1_title(zh_source), zh_body, "zh-CN"), encoding="utf-8"
    )
    bilingual_body = (
        '<p class="notice">Local bilingual editorial preview. Shopify has not been called.</p>'
        '<div class="columns"><section class="column" lang="en-US">'
        f"{en_body}</section><section class=\"column\" lang=\"zh-CN\">{zh_body}</section></div>"
    )
    (args.output_dir / f"{args.slug}.bilingual.html").write_text(
        document(f"{h1_title(en_source)} | 双语审阅", bilingual_body, "en", bilingual=True),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
