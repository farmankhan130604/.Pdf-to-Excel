# PDF-to-Excel Exhibitor Extractor

This repository provides a command-line tool to extract exhibitor listings from directory-style PDF books and export them to a clean spreadsheet.

## What it extracts

For each exhibitor block, the tool outputs:

- S. No.
- Company Name
- Address
- Hall/Stall
- Email
- Contact Person Name
- Contact Person Designation
- Company Profile
- Tel (optional helper column)
- Mobile (optional helper column)

## Features

- Parse specific page ranges from the source PDF (`--start-page`, `--end-page`).
- Handles entries where multiple fields are embedded in free-form text.
- Exports directly to `.xlsx` and optionally `.csv`.
- Designed for directories similar to the provided PLASTINDIA exhibitor layout.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 -m src.extract_exhibitors \
  --pdf "PLASTINDIA 2026 Exhibitor Directory (Main)-unlocked.pdf" \
  --start-page 73 \
  --end-page 542 \
  --output exhibitors.xlsx \
  --csv-output exhibitors.csv
```

### Notes on page numbers

- Use the PDF's 1-based page numbering for `--start-page` and `--end-page`.
- The tool validates the page range against the total page count.

## Output columns

The generated spreadsheet includes:

1. `S. No.`
2. `Company Name`
3. `Address`
4. `Hall/Stall`
5. `Email`
6. `Contact Person Name`
7. `Contact Person Designation`
8. `Company Profile`
9. `Tel`
10. `Mobile`

## Accuracy expectations

PDF text extraction quality depends on how text is encoded in the source document. This parser uses robust heuristics for common patterns, but a quick review of the resulting spreadsheet is recommended for final QA.
