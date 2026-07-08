"""Generate PDF of all psdnj.ir course detail pages."""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE_DIR = Path(__file__).resolve().parents[1]
SQL_JSON = BASE_DIR / "psdnj_courses.json"
OUTPUT_PDF = BASE_DIR / "courses-details.pdf"
DESKTOP_PDF = Path(r"C:\Users\mmrz\Desktop\courses-details.pdf")
FONT_PATH = Path(r"C:\Windows\Fonts\tahoma.ttf")
API_BASE = "https://psdnj.ir/wp-json/wp/v2/product"


def rtl(text: str) -> str:
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def clean_detail_text(raw: str) -> str:
    text = html.unescape(raw or "")
    text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = re.sub(r"</li\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.I)
    text = re.sub(r"<h[1-6][^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    # Fix mangled CRLF leftovers from SQL export
    text = re.sub(r"(?<=[!.:؟!])\s*rn(?=\S)", "\n", text)
    text = re.sub(r"\s*rn\s*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_all_from_api() -> list[dict]:
    courses: list[dict] = []
    page = 1
    while True:
        url = f"{API_BASE}?per_page=100&page={page}&status=publish&_fields=id,title,content"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            batch = json.loads(resp.read().decode("utf-8"))
        if not batch:
            break
        for item in batch:
            title = html.unescape(re.sub(r"<[^>]+>", "", item["title"]["rendered"])).strip()
            content = item["content"]["rendered"]
            if not title:
                continue
            courses.append(
                {
                    "id": item["id"],
                    "title": title,
                    "description": clean_detail_text(content),
                }
            )
        if len(batch) < 100:
            break
        page += 1
    return courses


def load_from_sql_json() -> list[dict]:
    data = json.loads(SQL_JSON.read_text(encoding="utf-8"))
    for item in data:
        item["description"] = clean_detail_text(item.get("description", ""))
    return data


def load_courses() -> list[dict]:
    try:
        courses = fetch_all_from_api()
        if courses:
            print(f"Loaded {len(courses)} courses from psdnj.ir API")
            return sorted(courses, key=lambda x: x["title"])
    except Exception as exc:
        print(f"API fetch failed: {exc}", file=sys.stderr)

    if SQL_JSON.exists():
        courses = load_from_sql_json()
        print(f"Loaded {len(courses)} courses from SQL export")
        return courses

    raise RuntimeError("No course data source available")


def para(text: str, style: ParagraphStyle) -> Paragraph:
    safe = rtl(text).replace("\n", "<br/>")
    return Paragraph(safe, style)


def build_pdf(courses: list[dict]) -> None:
    pdfmetrics.registerFont(TTFont("Tahoma", str(FONT_PATH)))

    header_style = ParagraphStyle(
        "Header",
        fontName="Tahoma",
        fontSize=11,
        leading=16,
        alignment=2,
        textColor=colors.white,
    )
    title_style = ParagraphStyle(
        "Title",
        fontName="Tahoma",
        fontSize=9,
        leading=13,
        alignment=2,
        textColor=colors.HexColor("#0F172A"),
    )
    body_style = ParagraphStyle(
        "Body",
        fontName="Tahoma",
        fontSize=8,
        leading=12,
        alignment=2,
    )

    rows = [
        [para("دوره", header_style), para("توضیحات", header_style)],
    ]
    for course in courses:
        rows.append(
            [
                para(course["title"], title_style),
                para(course["description"] or "—", body_style),
            ]
        )

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="جزئیات دوره‌های پژوهشسرا",
    )

    table = Table(rows, colWidths=[42 * mm, 138 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("FONTNAME", (0, 0), (-1, -1), "Tahoma"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    doc.build([Spacer(1, 1 * mm), table])
    DESKTOP_PDF.write_bytes(OUTPUT_PDF.read_bytes())
    print(f"PDF created: {OUTPUT_PDF} ({len(courses)} courses)")
    print(f"Copied to: {DESKTOP_PDF}")


def main() -> None:
    courses = load_courses()
    build_pdf(courses)


if __name__ == "__main__":
    main()
