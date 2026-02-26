from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable



FIELD_STOPWORDS = (
    "tel",
    "telephone",
    "mobile",
    "email",
    "website",
    "contact",
    "company profile",
)


@dataclass
class ExhibitorRecord:
    serial_no: int
    company_name: str
    address: str
    hall_stall: str
    email: str
    contact_person_name: str
    contact_person_designation: str
    company_profile: str
    tel: str
    mobile: str

    def to_row(self) -> dict[str, str | int]:
        return {
            "S. No.": self.serial_no,
            "Company Name": self.company_name,
            "Address": self.address,
            "Hall/Stall": self.hall_stall,
            "Email": self.email,
            "Contact Person Name": self.contact_person_name,
            "Contact Person Designation": self.contact_person_designation,
            "Company Profile": self.company_profile,
            "Tel": self.tel,
            "Mobile": self.mobile,
        }


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_into_entries(page_text: str) -> list[str]:
    """Split a page into exhibitor entries by identifying company-heading lines."""
    lines = [line.rstrip() for line in page_text.splitlines() if line.strip()]
    entries: list[list[str]] = []
    current: list[str] = []

    heading_pattern = re.compile(r"^(?:\d+\s+)?[A-Z0-9&.,'\-()/ ]{4,}$")

    for line in lines:
        is_heading = bool(heading_pattern.match(line.strip())) and not line.lower().startswith(
            ("tel", "email", "contact", "company profile", "website")
        )

        if is_heading and current:
            entries.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        entries.append(current)

    return ["\n".join(entry).strip() for entry in entries if entry]


def extract_field(pattern: str, text: str, flags: int = re.IGNORECASE | re.DOTALL) -> str:
    match = re.search(pattern, text, flags)
    if not match:
        return ""
    return normalize_whitespace(match.group(1))


def infer_company_name(lines: list[str]) -> str:
    if not lines:
        return ""
    first_line = lines[0].strip()
    return normalize_whitespace(re.sub(r"^\d+\s*", "", first_line))


def infer_address(lines: list[str]) -> str:
    if not lines:
        return ""

    address_lines: list[str] = []
    for line in lines[1:]:
        lowered = line.strip().lower()
        if any(lowered.startswith(token) for token in FIELD_STOPWORDS):
            break
        address_lines.append(line.strip())

    return normalize_whitespace(" ".join(address_lines))


def infer_hall_stall(block: str) -> str:
    hall_pattern = re.compile(
        r"\b([A-Z]{1,4}\d{0,2}\s*/\s*[A-Z]?\d{1,3})\b|\b([A-Z]\d{1,3}/[A-Z]?\d{1,3})\b",
        re.IGNORECASE,
    )
    for match in hall_pattern.finditer(block):
        candidate = match.group(0).replace(" ", "")
        if any(ch.isdigit() for ch in candidate) and "/" in candidate:
            return candidate.upper()
    return ""


def parse_contact_field(contact_text: str) -> tuple[str, str]:
    if not contact_text:
        return "", ""

    parts = [part.strip() for part in re.split(r"\s*[-–—,]\s*", contact_text, maxsplit=1)]
    if len(parts) == 2:
        return normalize_whitespace(parts[0]), normalize_whitespace(parts[1])
    return normalize_whitespace(contact_text), ""


def parse_exhibitor_block(block: str, serial_no: int) -> ExhibitorRecord:
    lines = [line for line in block.splitlines() if line.strip()]
    merged = "\n".join(lines)

    company_name = infer_company_name(lines)
    address = infer_address(lines)

    tel = extract_field(r"\bTel\s*:\s*(.*?)(?=\b(?:Mobile|Email|Website|Contact|Company Profile)\b|$)", merged)
    mobile = extract_field(r"\bMobile\s*:\s*(.*?)(?=\b(?:Email|Website|Contact|Company Profile)\b|$)", merged)
    email = extract_field(r"\bEmail\s*:\s*(.*?)(?=\b(?:Website|Contact|Company Profile)\b|$)", merged)
    contact = extract_field(r"\bContact\s*:\s*(.*?)(?=\b(?:Company Profile|Tel|Telephone|Mobile|Email|Website)\b|$)", merged)
    company_profile = extract_field(r"\bCompany\s*Profile\s*:\s*(.*)$", merged, re.IGNORECASE | re.DOTALL)

    contact_name, contact_designation = parse_contact_field(contact)

    hall_stall = infer_hall_stall(merged)

    return ExhibitorRecord(
        serial_no=serial_no,
        company_name=company_name,
        address=address,
        hall_stall=hall_stall,
        email=email,
        contact_person_name=contact_name,
        contact_person_designation=contact_designation,
        company_profile=normalize_whitespace(company_profile),
        tel=tel,
        mobile=mobile,
    )


def parse_pdf_entries(pdf_path: Path, start_page: int, end_page: int) -> list[ExhibitorRecord]:
    records: list[ExhibitorRecord] = []
    serial_no = 1

    import pdfplumber

    with pdfplumber.open(str(pdf_path)) as pdf:
        page_count = len(pdf.pages)
        if start_page < 1 or end_page < 1 or start_page > end_page or end_page > page_count:
            raise ValueError(
                f"Invalid page range {start_page}-{end_page}. PDF has {page_count} pages."
            )

        for page_index in range(start_page - 1, end_page):
            page = pdf.pages[page_index]
            text = page.extract_text() or ""
            if not text.strip():
                continue

            for block in split_into_entries(text):
                record = parse_exhibitor_block(block, serial_no)
                if record.company_name:
                    records.append(record)
                    serial_no += 1

    return records


def write_outputs(records: Iterable[ExhibitorRecord], output_path: Path, csv_output: Path | None = None) -> None:
    import pandas as pd

    rows = [record.to_row() for record in records]
    df = pd.DataFrame(rows)
    df.to_excel(output_path, index=False)

    if csv_output:
        df.to_csv(csv_output, index=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract exhibitor data from a PDF directory into Excel/CSV."
    )
    parser.add_argument("--pdf", required=True, type=Path, help="Path to source PDF file")
    parser.add_argument("--start-page", required=True, type=int, help="Start page (1-based)")
    parser.add_argument("--end-page", required=True, type=int, help="End page (1-based)")
    parser.add_argument("--output", required=True, type=Path, help="Output XLSX path")
    parser.add_argument("--csv-output", type=Path, default=None, help="Optional output CSV path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    records = parse_pdf_entries(args.pdf, args.start_page, args.end_page)
    write_outputs(records, args.output, args.csv_output)
    print(f"Extracted {len(records)} records -> {args.output}")


if __name__ == "__main__":
    main()
