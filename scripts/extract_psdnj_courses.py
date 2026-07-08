"""Extract published WooCommerce products from psdnj.ir SQL dump."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

SQL_PATH = Path(r"C:\Users\mmrz\Downloads\New folder\psdnjir_db_1782659638.sql")
OUTPUT_JSON = Path(r"D:\Projects\pazhooheshsaraa\psdnj_courses.json")


def unescape_sql(value: str) -> str:
    value = value.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    return value.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = re.sub(r"</li\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.I)
    text = re.sub(r"<h[1-6][^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_sql_value(text: str, pos: int) -> tuple[str | None, int]:
    while pos < len(text) and text[pos] in " \t\n\r":
        pos += 1
    if pos >= len(text):
        return None, pos
    if text[pos] == "N" and text[pos : pos + 4] == "NULL":
        return None, pos + 4
    if text[pos] == "'":
        pos += 1
        chars: list[str] = []
        while pos < len(text):
            ch = text[pos]
            if ch == "\\" and pos + 1 < len(text):
                chars.append(text[pos + 1])
                pos += 2
                continue
            if ch == "'":
                if pos + 1 < len(text) and text[pos + 1] == "'":
                    chars.append("'")
                    pos += 2
                    continue
                pos += 1
                break
            chars.append(ch)
            pos += 1
        return unescape_sql("".join(chars)), pos
    # bare number / token
    start = pos
    while pos < len(text) and text[pos] not in ",)":
        pos += 1
    return text[start:pos].strip(), pos


def parse_tuple(text: str, pos: int) -> tuple[list, int]:
    if text[pos] != "(":
        raise ValueError("tuple must start with (")
    pos += 1
    values: list = []
    while pos < len(text):
        while pos < len(text) and text[pos] in " \t\n\r":
            pos += 1
        if text[pos] == ")":
            return values, pos + 1
        value, pos = parse_sql_value(text, pos)
        values.append(value)
        while pos < len(text) and text[pos] in " \t\n\r":
            pos += 1
        if pos < len(text) and text[pos] == ",":
            pos += 1
    raise ValueError("unterminated tuple")


def iter_posts_rows(blob: str):
    marker = "INSERT INTO `wp_posts` VALUES "
    start = 0
    while True:
        idx = blob.find(marker, start)
        if idx == -1:
            return
        pos = idx + len(marker)
        while pos < len(blob):
            while pos < len(blob) and blob[pos] in " \t\n\r":
                pos += 1
            if pos >= len(blob) or blob[pos] != "(":
                break
            row, pos = parse_tuple(blob, pos)
            yield row
            while pos < len(blob) and blob[pos] in " \t\n\r":
                pos += 1
            if pos < len(blob) and blob[pos] == ",":
                pos += 1
                continue
            if pos < len(blob) and blob[pos] == ";":
                pos += 1
            break
        start = pos


def main() -> None:
    blob = SQL_PATH.read_text(encoding="utf-8", errors="ignore")
    products: list[dict] = []

    for row in iter_posts_rows(blob):
        if len(row) < 22:
            continue
        post_status = row[7]
        post_type = row[20]
        if post_status != "publish" or post_type != "product":
            continue
        title = (row[5] or "").strip()
        content = row[4] or ""
        if not title:
            continue
        products.append(
            {
                "id": int(row[0]),
                "title": title,
                "description": strip_html(content),
            }
        )

    products.sort(key=lambda x: x["title"])
    OUTPUT_JSON.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(products)} courses -> {OUTPUT_JSON}")
    for p in products[:8]:
        print(f"- {p['title'][:70]} | {len(p['description'])} chars")


if __name__ == "__main__":
    main()
