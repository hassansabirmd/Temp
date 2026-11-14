# HY Arrows — TOC tools

Adds a hyperlinked Table of Contents to the MehlmanMedical **HY Arrows** PDF.

## Usage

```bash
pip install -r requirements.txt
python scripts/add_toc_to_hy_arrows.py \
  --input input/HY_Arrows.pdf \
  --output output/HY_Arrows_with_TOC.pdf
```

The script inserts TOC pages at the start of the PDF. Each entry uses short topic names in the form `High aldosterone --- Page 4` and links to the corresponding question page. Page numbers in the TOC match the printed page numbers in the original document.
