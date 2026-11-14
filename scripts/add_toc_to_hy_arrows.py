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

# Short, complete clinical titles — never truncated mid-word.
TITLES = {
    1: "High aldosterone",
    2: "Low aldosterone",
    3: "Lisinopril",
    4: "Valsartan",
    5: "Spironolactone",
    6: "Enalapril",
    7: "Renal artery stenosis",
    8: "Addison disease",
    9: "Primary adrenal insufficiency",
    10: "Exogenous Cushing syndrome",
    11: "Waterhouse-Friderichsen syndrome",
    12: "Adrenal Cushing (low ACTH)",
    13: "Pituitary Cushing disease",
    14: "Ectopic ACTH production",
    15: "Adrenal adenoma (Cushing)",
    16: "Sheehan syndrome",
    17: "Pituitary adenoma + fracture",
    18: "High vasopressin (ADH)",
    19: "Low vasopressin (ADH)",
    20: "SIADH (smoker)",
    21: "Psychogenic polydipsia",
    22: "Central diabetes insipidus",
    23: "Nephrogenic DI (lithium)",
    24: "Marathon runner / dehydration",
    25: "Chronic NSAID use",
    26: "Mannitol infusion",
    27: "Primary vs secondary hyperthyroidism",
    28: "Primary vs secondary hypothyroidism",
    29: "Graves disease",
    30: "Hashimoto hypothyroidism",
    31: "Subacute (de Quervain) thyroiditis",
    32: "Medullary thyroid carcinoma",
    33: "Injecting T3",
    34: "Injecting T4 (levothyroxine)",
    35: "Subclinical hypothyroidism",
    36: "Euthyroid sick syndrome",
    37: "Pregnancy thyroid changes",
    38: "TBG deficiency",
    39: "Postpartum thyroiditis",
    40: "Lithium thyroid effects",
    41: "Primary hypo- vs hyperparathyroidism",
    42: "MEN / kidney stone",
    43: "Post-thyroidectomy hypoparathyroidism",
    44: "Hypomagnesemia hypocalcemia",
    45: "MEN1 (ulcers + impotence)",
    46: "DiGeorge syndrome",
    47: "CKD secondary hyperparathyroidism",
    48: "Acute tubular necrosis",
    49: "Chronic renal failure",
    50: "Granulomatosis with polyangiitis",
    51: "Parathyroid adenoma",
    52: "Calcium-sensing receptor mutation",
    53: "Familial hypocalciuric hypercalcemia",
    54: "Cinacalcet",
    55: "Albright hereditary osteodystrophy (male)",
    56: "Albright hereditary osteodystrophy (female)",
    57: "Tertiary hyperparathyroidism",
    58: "Vitamin D receptor mutation",
    59: "PTHrP / squamous cell lung cancer",
    60: "Renal cell carcinoma (PTHrP)",
    61: "Vitamin D deficiency / rickets",
    62: "Osteoporosis (elderly woman)",
    63: "Osteoporosis densitometry",
    64: "Paget disease of bone",
    65: "Metastatic breast cancer",
    66: "Multiple myeloma",
    67: "Sarcoidosis",
    68: "Sarcoidosis with fever",
    69: "Sarcoidosis + erythema nodosum",
    70: "Parathyroid adenoma (young)",
    71: "Cystic fibrosis + steatorrhea",
    72: "Vitamin D deficiency (alcoholic)",
    73: "Vitamin D deficiency (no sun)",
    74: "Menopause / perimenopause",
    75: "Turner syndrome",
    76: "Female athlete triad / anorexia",
    77: "Klinefelter syndrome",
    78: "PCOS (24F)",
    79: "PCOS (28F)",
    80: "Anabolic steroid use",
    81: "Androgen insensitivity syndrome",
    82: "Precocious puberty",
    83: "Prolactinoma",
    84: "Pituitary stalk transection",
    85: "Down syndrome triscreen (CVS)",
    86: "Down syndrome triscreen risk",
    87: "Hyperemesis gravidarum",
    88: "Laxative abuse",
    89: "Furosemide abuse",
    90: "Spironolactone abuse",
    91: "Hydrochlorothiazide",
    92: "Expired tetracyclines (Fanconi)",
    93: "Chronic diuretic abuse",
    94: "ATN after intraoperative hypotension",
    95: "Acetazolamide (altitude)",
    96: "21-hydroxylase deficiency",
    97: "11-hydroxylase deficiency",
    98: "17-hydroxylase deficiency",
    99: "21-hydroxylase (salt-wasting female)",
    100: "CAH with hypertension",
    101: "DKA (new onset)",
    102: "DKA (missed insulin)",
    103: "DKA after viral illness",
    104: "Iron overdose",
    105: "Aspirin overdose (early)",
    106: "Aspirin overdose (later)",
    107: "PE after C-section",
    108: "Acute asthma exacerbation",
    109: "Asthma with fatigue / CO2 rise",
    110: "Hyperventilation / panic",
    111: "COPD exacerbation",
    112: "Stable COPD",
    113: "Morphine / hypoventilation",
    114: "Congestive heart failure",
    115: "Cystic fibrosis",
    116: "Scleroderma / PAH",
    117: "Pulmonary embolism (OCP + smoking)",
    118: "Acute pancreatitis",
    119: "Idiopathic pulmonary fibrosis",
    120: "Normal aging PFTs",
    121: "Alpha-1 antitrypsin deficiency",
    122: "Neonatal RDS (surfactant)",
    123: "COPD physiology",
    124: "Exercise / no water intake",
    125: "Left heart failure (orthopnea)",
    126: "Primary pulmonary hypertension",
    127: "CHF pleural effusion",
    128: "Enalapril in diabetes",
    129: "Cold water immersion",
    130: "VSD repair",
    131: "ASD (fixed splitting S2)",
    132: "VSD (holosystolic murmur)",
    133: "Standing from supine",
    134: "Propranolol",
    135: "Nitrates",
    136: "Nifedipine",
    137: "Systolic heart failure",
    138: "Diastolic heart failure",
    139: "Anterior STEMI / cardiogenic shock",
    140: "Anaphylactic shock",
    141: "Septic shock",
    142: "Hypovolemic shock",
    143: "Cardiogenic shock (viral myocarditis)",
    144: "ITP (post-viral)",
    145: "Hemophilia A",
    146: "von Willebrand disease",
    147: "APL / DIC (t15;17)",
    148: "Amniotic fluid embolism / DIC",
    149: "Vitamin K deficiency (neonate)",
    150: "Uremic platelet dysfunction",
    151: "HELLP / preeclampsia",
    152: "Iron deficiency anemia",
    153: "Anemia of chronic disease (JIA)",
    154: "Alpha-thalassemia",
    155: "Restless legs / iron deficiency",
    156: "Iron deficiency O2 content",
    157: "Gilbert syndrome",
    158: "Obstructive jaundice (bile duct)",
    159: "G6PD deficiency (dapsone)",
    160: "Fed state enzymes (turkey dinner)",
    161: "Fed state enzymes (continued)",
    162: "Type 1 diabetes / insulin lack",
    163: "Glucokinase vs hexokinase",
    164: "Oxytocin signaling",
    165: "Cimetidine signaling",
    166: "Refeeding syndrome",
    167: "Bacterial meningitis (CSF)",
    168: "Cryptococcal meningitis (CSF)",
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


def build_toc_entries(questions: list[dict]) -> list[dict]:
    missing = [q["qnum"] for q in questions if q["qnum"] not in TITLES]
    if missing:
        raise RuntimeError(f"Missing TOC titles for questions: {missing}")
    return [{**q, "title": TITLES[q["qnum"]]} for q in questions]


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
            title_w = fitz.get_text_length(title, fontname="helv", fontsize=font_size)
            if title_w > max_title_width:
                raise RuntimeError(
                    f"Title too long for one line (Q{entry['qnum']}): {title!r}"
                )

            page.insert_text(
                (margin_x, y), title, fontsize=font_size, fontname="helv", color=LINK_BLUE
            )
            pl_w = fitz.get_text_length(page_label, fontname="helv", fontsize=font_size)
            page.insert_text(
                (right_col_x - pl_w, y),
                page_label,
                fontsize=font_size,
                fontname="helv",
                color=DARK,
            )

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
