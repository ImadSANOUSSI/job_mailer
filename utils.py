import os
import csv
import re
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from email_validator import validate_email as ev_validate_email, EmailNotValidError
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("job_mailer")

def get_env(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    v = os.getenv(name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Missing required env var: {name}")
    return v

def get_openai_client() -> OpenAI:
    key = get_env("OPENAI_API_KEY", required=True)
    return OpenAI(api_key=key)

def read_csv(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return rows
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows

def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("")
        return
    headers = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)

def validate_email(addr: str) -> bool:
    if not addr:
        return False
    try:
        ev_validate_email(addr, allow_smtputf8=True)
        return True
    except EmailNotValidError:
        return False

def extract_emails(text: str) -> List[str]:
    if not text:
        return []
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    found = re.findall(pattern, text)
    return sorted(set(found))

def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._") or "file"
