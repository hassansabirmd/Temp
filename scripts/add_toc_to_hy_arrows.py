#!/usr/bin/env python3
"""Add a hyperlinked Table of Contents to HY Arrows PDF."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import fitz  # pymupdf

TEAL = (0.0, 0.45, 0.45)
DARK = (0.12, 0.12, 0.12)
GRAY = (0.35, 0.35, 0.35)
LINK_BLUE = (0.05, 0.25, 0.55)

# Short titles matching the requested TOC naming style for early entries,
# plus clearer clinical names for selected vignettes.
OVERRIDES = {
    1: "High aldosterone",
    2: "Low aldosterone",
    3: "Lisinopril",
    4: "Valsartan",
    5: "Spironolactone",
    6: "Enalapril",
    7: "Abdominal bruit + hypertension",
    8: "Addison disease (hyperpigmentation + eosinophilia)",
    9: "Primary adrenal insufficiency (ACTH stim)",
    10: "Exogenous Cushing (RA on steroids)",
    11: "Waterhouse-Friderichsen syndrome",
    12: "Adrenal Cushing (low ACTH)",
    13: "Pituitary Cushing / Cushing disease",
    14: "Ectopic ACTH (small cell / paraneoplastic)",
    15: "Adrenal adenoma (Cushing)",
    16: "Sheehan syndrome",
    17: "Pituitary adenoma + vertebral fracture",
    18: "High vasopressin (ADH)",
    19: "Low vasopressin (ADH)",
    20: "SIADH (smoker + confusion)",
    21: "Psychogenic polydipsia",
    22: "Central diabetes insipidus (head trauma)",
    23: "Lithium / nephrogenic DI (bipolar)",
    24: "Marathon runner (volume depletion)",
    25: "Chronic NSAID use",
    26: "Mannitol infusion",
    27: "Primary vs secondary hyperthyroidism",
    28: "Primary vs secondary hypothyroidism",
    33: "Injecting T3",
    34: "Injecting T4 (levothyroxine)",
    41: "Primary hypo- vs hyperparathyroidism",
}


def extract_questions(doc: fitz.Document) -> list[dict]:
    questions: list[dict] = []
    skip = {
        "MEHLMANMEDICAL.COM",
        "YouTube",
        "@mehlmanmedical",
        "Instagram",
        "@mehlman_medical",
        "MEHLMANMEDICAL",
        "HY ARROWS",
    }
    for i, page in enumerate(doc):
        lines = [l.strip() for l in page.get_text().splitlines() if l.strip()]
        body_lines = []
        for line in lines:
            if line in skip or re.fullmatch(r"\d+", line):
                continue
            body_lines.append(line)
        body = " ".join(body_lines)
        match = re.match(r"^(\d+)\.\s+(.+)", body)
        if not match:
            continue
        qnum = int(match.group(1))
        end = body.find("?")
        qtext = body[: end + 1] if end != -1 else body
        qtext_clean = re.sub(r"^\d+\.\s*", "", qtext)
        questions.append(
            {
                "orig_page": i + 1,
                "page_index": i,
                "qnum": qnum,
                "qtext": qtext_clean,
            }
        )
    return questions


def clean_parens(s: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*", " ", s)


def make_title(qtext: str) -> str:
    t = re.sub(r"\s+", " ", qtext).strip()

    m = re.match(r"(?i)Patient has ([^.]+)\.", t)
    if m:
        return m.group(1).strip().capitalize()

    m = re.match(
        r"(?i)(?:If a patient is given|Patient is given)\s+([A-Za-z0-9\-]+)", t
    )
    if m:
        return m.group(1).strip().capitalize()

    m = re.match(r"(?i)Patient is injecting\s+(.+?)(?:\.|$)", t)
    if m:
        return f"Injecting {clean_parens(m.group(1)).strip()}"

    m = re.match(r"(?i)Patient with\s+(.+?)(?:\.|$)", t)
    if m:
        return m.group(1).strip().rstrip(".").capitalize()

    m = re.match(r"(?i)In (primary vs secondary \w+)", t)
    if m:
        return m.group(1).strip().capitalize()

    m = re.match(r"(?i)A researcher is comparing\s+(.+?)(?:\.|,| with |$)", t)
    if m:
        return f"Comparing {m.group(1).strip()}"

    m = re.search(
        r"(?i)if\s+(vasopressin|anti-diuretic hormone|ADH)[^(]*\s+is\s+"
        r"(increased|decreased|high|low)",
        t,
    )
    if m:
        return f"Vasopressin {m.group(2).lower()}"

    m = re.search(
        r"(?i)if\s+(.+?)\s+is\s+(increased|decreased|high|low|administered|given)\b",
        t,
    )
    if m and not re.match(r"(?i)\d+[MF]\b", t):
        subj = re.sub(r"\s+", " ", clean_parens(m.group(1))).strip()
        if len(subj) < 40:
            return f"{subj} {m.group(2)}".strip().capitalize()

    core = re.split(r"(?i)\s*[Ww]hat are the (?:most likely )?arrows", t)[0]
    core = re.split(r"(?i)\s*[Ww]hat will happen", core)[0]
    core = re.split(r"(?i)\s*[Ww]hat change will", core)[0]
    core = re.split(r"(?i)\s*[Aa]s a result", core)[0]
    core = re.split(r"(?i);\s*if\s+", core)[0]
    core = re.split(r"(?i)\.\s*[Ww]hat\b", core)[0]
    core = re.split(r"(?i)\.\s*[Cc]ompared\b", core)[0]
    core = core.strip(" ;,.")

    if " + " in core:
        parts = [p.strip().rstrip(".") for p in core.split(" + ")]
        selected: list[str] = []
        for part in parts:
            if re.match(r"(?i)^(what|which|if)\b", part):
                break
            if len(part) > 55:
                part = part[:52].rstrip() + "…"
            selected.append(part)
            if len(" + ".join(selected)) > 68 or len(selected) >= 3:
                break
        title = " + ".join(selected)
        return title[:69].rstrip() + "…" if len(title) > 72 else title

    return core[:69].rstrip() + "…" if len(core) > 72 else (core or t[:70])


def build_toc_entries(questions: list[dict]) -> list[dict]:
    entries = []
    for q in questions:
        title = OVERRIDES.get(q["qnum"]) or make_title(q["qtext"])
        entries.append({**q, "title": title.strip().rstrip(".")})
    return entries


def create_toc_pages(
    entries: list[dict], page_width: float, page_height: float
) -> tuple[fitz.Document, list[dict], int]:
    toc = fitz.open()
    link_specs: list[dict] = []

    margin_x = 48
    margin_top = 56
    margin_bottom = 48
    title_block = 70
    line_h = 13.2
    font_size = 9.5
    usable_h = page_height - margin_top - margin_bottom - title_block
    rows_per_page = int(usable_h // line_h)

    chunks = [
        entries[i : i + rows_per_page] for i in range(0, len(entries), rows_per_page)
    ]
    toc_page_count = len(chunks)

    for page_i, chunk in enumerate(chunks):
        page = toc.new_page(width=page_width, height=page_height)
        page.draw_rect(fitz.Rect(0, 0, page_width, 42), color=None, fill=TEAL)
        page.insert_text(
            (margin_x, 28), "MEHLMANMEDICAL", fontsize=11, fontname="helv", color=(1, 1, 1)
        )
        page.insert_text(
            (page_width - margin_x - 70, 28),
            "HY ARROWS",
            fontsize=10,
            fontname="helv",
            color=(1, 1, 1),
        )

        header = "Table of Contents"
        if toc_page_count > 1:
            header += f" ({page_i + 1}/{toc_page_count})"
        page.insert_text(
            (margin_x, margin_top + 18), header, fontsize=18, fontname="helv", color=TEAL
        )
        page.insert_text(
            (margin_x, margin_top + 36),
            "Click any entry to jump to that question.",
            fontsize=9,
            fontname="helv",
            color=GRAY,
        )

        y = margin_top + title_block
        right_col_x = page_width - margin_x
        for entry in chunk:
            title = entry["title"]
            page_label = f"Page {entry['orig_page']}"
            max_title_width = right_col_x - margin_x - 70
            display = title
            while (
                fitz.get_text_length(display, fontname="helv", fontsize=font_size)
                > max_title_width
                and len(display) > 10
            ):
                display = display[:-2] + "…"

            page.insert_text(
                (margin_x, y), display, fontsize=font_size, fontname="helv", color=LINK_BLUE
            )
            pl_w = fitz.get_text_length(page_label, fontname="helv", fontsize=font_size)
            page.insert_text(
                (right_col_x - pl_w, y),
                page_label,
                fontsize=font_size,
                fontname="helv",
                color=DARK,
            )

            title_w = fitz.get_text_length(display, fontname="helv", fontsize=font_size)
            dots_start = margin_x + title_w + 6
            dots_end = right_col_x - pl_w - 6
            if dots_end > dots_start + 10:
                page.draw_line(
                    fitz.Point(dots_start, y - 2),
                    fitz.Point(dots_end, y - 2),
                    color=(0.75, 0.75, 0.75),
                    width=0.5,
                    dashes="[1 2]",
                )

            link_specs.append(
                {
                    "toc_page_index": page_i,
                    "rect": fitz.Rect(margin_x - 2, y - font_size - 1, right_col_x + 2, y + 3),
                    "target_orig_index": entry["page_index"],
                }
            )
            y += line_h

        page.insert_text(
            (margin_x, page_height - 28),
            "HY Arrows — Table of Contents",
            fontsize=8,
            fontname="helv",
            color=GRAY,
        )

    return toc, link_specs, toc_page_count


def add_toc(src_path: Path, out_path: Path) -> dict:
    src = fitz.open(src_path)
    page_width, page_height = src[0].rect.width, src[0].rect.height
    questions = extract_questions(src)
    if len(questions) != 168:
        raise RuntimeError(f"Expected 168 questions, found {len(questions)}")
    entries = build_toc_entries(questions)
    toc_doc, link_specs, toc_page_count = create_toc_pages(
        entries, page_width, page_height
    )

    out = fitz.open()
    out.insert_pdf(toc_doc)
    out.insert_pdf(src)

    for spec in link_specs:
        out[spec["toc_page_index"]].insert_link(
            {
                "kind": fitz.LINK_GOTO,
                "from": spec["rect"],
                "page": spec["target_orig_index"] + toc_page_count,
                "to": fitz.Point(0, 0),
            }
        )

    outline = [[1, "Table of Contents", 0]]
    for entry in entries:
        outline.append(
            [
                1,
                f"{entry['title']} — Page {entry['orig_page']}",
                entry["page_index"] + toc_page_count,
            ]
        )
    out.set_toc(outline)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path, deflate=True, garbage=3)

    stats = {
        "toc_pages": toc_page_count,
        "total_pages": len(out),
        "links": len(link_specs),
        "first_entries": [
            f"{e['title']} --- Page {e['orig_page']}" for e in entries[:4]
        ],
    }
    out.close()
    toc_doc.close()
    src.close()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("input/HY_Arrows.pdf"),
        help="Source HY Arrows PDF",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/HY_Arrows_with_TOC.pdf"),
        help="Output PDF path",
    )
    args = parser.parse_args()
    stats = add_toc(args.input, args.output)
    print(f"Wrote {args.output}")
    print(
        f"TOC pages: {stats['toc_pages']}, total pages: {stats['total_pages']}, "
        f"links: {stats['links']}"
    )
    print("First entries:")
    for line in stats["first_entries"]:
        print(f"  {line}")


if __name__ == "__main__":
    main()
