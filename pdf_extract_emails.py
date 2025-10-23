import os
import argparse
from typing import List, Dict
from pypdf import PdfReader
from utils import logger, write_csv, extract_emails


def extract_from_pdf(path: str) -> List[str]:
    if not os.path.exists(path):
        logger.error(f"PDF not found: {path}")
        return []
    emails: List[str] = []
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            text = page.extract_text() or ""
            emails.extend(extract_emails(text))
    except Exception as ex:
        logger.error(f"Failed to read {path}: {ex}")
        return []
    return sorted(set(emails))


def main() -> None:
    p = argparse.ArgumentParser(description="Extract email addresses from PDF(s) and write contacts.csv")
    p.add_argument("--pdf", nargs="+", required=True, help="One or more PDF files")
    p.add_argument("--out", default="contacts.csv")
    a = p.parse_args()

    all_emails: List[str] = []
    for pdf in a.pdf:
        found = extract_from_pdf(pdf)
        logger.info(f"{pdf}: {len(found)} emails")
        all_emails.extend(found)

    rows: List[Dict[str, str]] = []
    for e in sorted(set(all_emails)):
        rows.append({"email": e, "company": "", "post_url": "", "job_post_text": ""})

    write_csv(a.out, rows)
    logger.info(f"Wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()
