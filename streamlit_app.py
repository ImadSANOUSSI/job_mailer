import os
import io
import time
import tempfile
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from pypdf import PdfReader
from docx import Document
from utils import extract_emails, safe_filename, get_env, logger
from send_mail import gen_subject_body, send_email

# --- Helpers ---
FIELDS = {
    "Data/AI": [
        "data", "ai", "machine learning", "ml", "deep learning", "python", "pandas",
        "data science", "nlp", "llm", "apprentissage automatique", "intelligence artificielle"
    ],
    "Cybersecurity": [
        "security", "cyber", "cybersecurity", "pentest", "siem", "soc", "owasp",
        "sécurité", "infosec", "threat", "vulnerability", "forensics"
    ],
    "Dev": [
        "developer", "dev", "frontend", "backend", "fullstack", "java", "javascript",
        "typescript", "react", "node", "spring", "api", "microservices", "golang", "rust"
    ],
}


def text_from_pdf(file_like: io.BytesIO) -> str:
    text = []
    reader = PdfReader(file_like)
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text)


def text_from_docx(file_like: io.BytesIO) -> str:
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(file_like.read())
        tmp_path = tmp.name
    try:
        d = Document(tmp_path)
        return "\n".join(p.text for p in d.paragraphs)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def text_from_url(url: str) -> str:
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        return soup.get_text(" ")
    except Exception:
        return ""


def find_emails_with_context(text: str, context_window: int = 80) -> List[Tuple[str, str]]:
    results: List[Tuple[str, str]] = []
    if not text:
        return results
    emails = extract_emails(text)
    for e in emails:
        idx = text.lower().find(e.lower())
        if idx >= 0:
            start = max(0, idx - context_window)
            end = min(len(text), idx + len(e) + context_window)
            snippet = text[start:end].replace("\n", " ")
        else:
            snippet = ""
        results.append((e, snippet))
    return results

def company_from_email(addr: str) -> str:
    try:
        local, domain = addr.split("@", 1)
        parts = domain.lower().split('.')
        if len(parts) >= 2:
            sld = parts[-2]  # second-level domain
        else:
            sld = parts[0]
        # Common freemail domains -> no company
        if sld in {"gmail", "yahoo", "hotmail", "outlook", "live", "icloud", "proton", "pm", "aol"}:
            return ""
        return sld
    except Exception:
        return ""

def filter_by_field(rows: List[Dict[str, str]], field: str, extra_keywords: List[str]) -> List[Dict[str, str]]:
    keywords = set([k.lower() for k in FIELDS.get(field, [])] + [k.lower() for k in extra_keywords])
    if not keywords:
        return rows
    out: List[Dict[str, str]] = []
    for r in rows:
        snippet = (r.get("context") or "").lower()
        if any(k in snippet for k in keywords):
            out.append(r)
    return out


st.set_page_config(page_title="Job Mailer", page_icon="✉️", layout="wide")
st.title("Job Mailer – Streamlit")

with st.sidebar:
    st.header("Extraction sources")
    pdf_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)
    docx_files = st.file_uploader("Upload DOCX files", type=["docx"], accept_multiple_files=True)
    url_input = st.text_area("Paste URLs (one per line)", height=100)

    st.header("Field & Filtering")
    field = st.radio("Choose field", ["Data/AI", "Cybersecurity", "Dev"], index=0)
    custom_kw = st.text_input("Extra keywords (comma-separated)", value="")

    st.header("Email Sending")
    smtp_host = st.text_input("SMTP_HOST", value=os.getenv("SMTP_HOST", "smtp.gmail.com"))
    smtp_port = st.number_input("SMTP_PORT", value=int(os.getenv("SMTP_PORT", "587")))
    smtp_user = st.text_input("SMTP_USER", value=os.getenv("SMTP_USER", ""))
    smtp_pass = st.text_input("SMTP_PASS", type="password", value=os.getenv("SMTP_PASS", ""))
    from_name = st.text_input("FROM_NAME", value=os.getenv("FROM_NAME", "Candidate"))

    st.header("Attachments & Content")
    cv_upload = st.file_uploader("Upload your CV (PDF)", type=["pdf"], accept_multiple_files=False)
    template_upload = st.file_uploader("Upload lettre template (DOCX)", type=["docx"], accept_multiple_files=False)
    job_post_text = st.text_area("Job description (optional; leave blank to use template as-is)", height=200)

    dry_run = st.checkbox("Dry run (do not send emails)", value=True)

extract_btn = st.button("1) Extract emails")

if extract_btn:
    all_rows: List[Dict[str, str]] = []

    # PDFs
    for f in pdf_files or []:
        try:
            text = text_from_pdf(f)
            for email, ctx in find_emails_with_context(text):
                all_rows.append({"email": email, "source": f.name, "context": ctx})
        except Exception as ex:
            st.warning(f"Failed reading PDF {f.name}: {ex}")

    # DOCX
    for f in docx_files or []:
        try:
            text = text_from_docx(f)
            for email, ctx in find_emails_with_context(text):
                all_rows.append({"email": email, "source": f.name, "context": ctx})
        except Exception as ex:
            st.warning(f"Failed reading DOCX {f.name}: {ex}")

    # URLs
    for u in (url_input or "").splitlines():
        u = u.strip()
        if not u:
            continue
        text = text_from_url(u)
        for email, ctx in find_emails_with_context(text):
            all_rows.append({"email": email, "source": u, "context": ctx})

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["email"]).reset_index(drop=True)
    st.session_state["emails_df"] = df
    st.success(f"Extracted {len(df)} unique emails")

# Show and filter
emails_df: pd.DataFrame = st.session_state.get("emails_df")
if emails_df is not None:
    st.subheader("Extracted emails (raw)")
    st.dataframe(emails_df, use_container_width=True, height=250)

    extra_keywords = [k.strip() for k in (custom_kw or "").split(",") if k.strip()]
    filtered_rows = filter_by_field(emails_df.to_dict(orient="records"), field, extra_keywords)
    filt_df = pd.DataFrame(filtered_rows).drop_duplicates(subset=["email"]).reset_index(drop=True)

    st.subheader(f"Filtered by field: {field}")
    st.dataframe(filt_df, use_container_width=True, height=250)

    st.write(f"Total filtered emails: {len(filt_df)}")

    # 2) Send emails section
    st.markdown("---")
    st.header("2) Send emails to filtered list")
    send_btn = st.button("Send emails now")

    if send_btn:
        # Validations
        if len(filt_df) == 0:
            st.error("No emails to send.")
            st.stop()
        if not cv_upload or not template_upload:
            st.error("Please upload your CV (PDF) and lettre template (DOCX).")
            st.stop()
        if not smtp_host or not smtp_port or not smtp_user or not smtp_pass:
            st.error("Please fill SMTP credentials.")
            st.stop()
        # Job description is optional; if empty, letter uses template, and email uses generic content

        # Save uploads to temp paths
        os.makedirs("tmp_uploads", exist_ok=True)
        cv_path = os.path.join("tmp_uploads", safe_filename(cv_upload.name))
        with open(cv_path, "wb") as f:
            f.write(cv_upload.read())
        template_path = os.path.join("tmp_uploads", safe_filename(template_upload.name))
        with open(template_path, "wb") as f:
            f.write(template_upload.read())
        os.environ["CV_PATH"] = cv_path
        os.environ["TEMPLATE_PATH"] = template_path

        # Prepare letters output (we will copy the uploaded template as-is with a new name)
        out_letters = "out_letters"
        os.makedirs(out_letters, exist_ok=True)

        sent = 0
        errors = 0
        progress = st.progress(0)
        status_area = st.empty()

        for i, row in filt_df.iterrows():
            email = row["email"].strip()
            company = "Entreprise"
            try:
                # Decide attachment name from email -> company, else fallback
                comp = company_from_email(email)
                ext = os.path.splitext(template_path)[1] or ".docx"
                base_name = f"lettre_{comp}" if comp else "lettre_de_motivation"
                letter_name = safe_filename(base_name) + ext
                letter_path = os.path.join(out_letters, letter_name)
                # Copy template as-is to the target name (no modification)
                with open(template_path, "rb") as src, open(letter_path, "wb") as dst:
                    dst.write(src.read())
                # Subject/body (generic if no job description)
                sb = gen_subject_body(job_post_text, comp or "")
                attachments = [cv_path, letter_path]
                if dry_run:
                    logger.info(f"DRY RUN -> To: {email} | Subject: {sb['subject']} | Attachments: {attachments}")
                else:
                    send_email(smtp_host, int(smtp_port), smtp_user, smtp_pass, from_name, email, sb["subject"], sb["body"], attachments)
                sent += 1
                status_area.info(f"Sent {sent}/{len(filt_df)} to {email}")
            except Exception as ex:
                errors += 1
                status_area.error(f"Error sending to {email}: {ex}")
            finally:
                progress.progress(int(((i + 1) / max(1, len(filt_df))) * 100))
                time.sleep(0.1)

        if dry_run:
            st.success(f"DRY RUN complete. Would have processed {sent} emails. Errors: {errors}")
        else:
            st.success(f"Done. Sent: {sent}. Errors: {errors}")

st.markdown("---")
st.caption("Use responsibly. Ensure consent and compliance with applicable laws.")
