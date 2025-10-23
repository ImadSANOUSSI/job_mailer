import os
import argparse
import time
import json
import re
import requests
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from utils import logger, read_csv, write_csv, extract_emails


def linkedin_api_search(query: str) -> List[Dict[str, Any]]:
    client_id = os.getenv("LINKEDIN_CLIENT_ID", "")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "")
    if not client_id or not client_secret or not redirect_uri:
        logger.warning("LinkedIn API env vars missing; API mode unavailable")
        return []
    logger.info("LinkedIn API placeholder: configure OAuth and endpoints as permitted.")
    return []


def selenium_collect(urls: List[str]) -> List[Dict[str, Any]]:
    opts = Options()
    opts.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opts)
    out: List[Dict[str, Any]] = []
    try:
        for u in urls:
            try:
                driver.get(u)
                time.sleep(3)
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")
                text = soup.get_text(" ")
                emails = extract_emails(text)
                if emails:
                    for e in emails:
                        out.append({"email": e, "post_url": u})
            except Exception as ex:
                logger.error(f"Error processing {u}: {ex}")
    finally:
        driver.quit()
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Collect emails associated with LinkedIn posts.")
    p.add_argument("--mode", choices=["api", "selenium"], required=True)
    p.add_argument("--query", default="")
    p.add_argument("--input", default="")
    p.add_argument("--out", default="contacts.csv")
    a = p.parse_args()

    rows: List[Dict[str, Any]] = []
    if a.mode == "api":
        rows = linkedin_api_search(a.query)
    else:
        urls: List[str] = []
        if a.input:
            for r in read_csv(a.input):
                u = (r.get("url") or r.get("post_url") or "").strip()
                if u:
                    urls.append(u)
        urls = list(dict.fromkeys(urls))
        rows = selenium_collect(urls)

    write_csv(a.out, rows)
    logger.info(f"Wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()
