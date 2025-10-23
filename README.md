# Job Mailer

## Overview

- **Script D (`pdf_extract_emails.py`)**: Extracts emails from one or more PDFs and writes a `contacts.csv` compatible with `send_mail.py`.
- **Streamlit App (`streamlit_app.py`)**: Web UI to upload PDFs or URLs, extract and filter emails by field, upload CV and template, enter SMTP creds, and send emails with custom subject and body.

## Legal and Ethical Notes

- **Email**: Comply with anti-spam laws. Only contact addresses you are allowed to, include an opt-out, and respect consent.

## Project Layout

```
job-mailer/
├─ README.md
├─ requirements.txt
├─ templates/
│  └─ lettre_template.docx  # Placeholder (ignored by Git)
│  └─ cv.pdf                # Placeholder (ignored by Git)
├─ send_mail.py
├─ pdf_extract_emails.py
└─ streamlit_app.py
```

## Setup

```
python -m venv venv
venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
```

All configuration is done in the Streamlit app UI.

## Usage

### Streamlit app (end-to-end, recommended)
```
streamlit run streamlit_app.py
```
In the sidebar:
- Upload PDFs and/or paste URLs.
- Choose field (Data/AI, Cybersecurity, Dev) and optional extra keywords.
- Upload your CV (PDF) and template (PDF).
- Enter `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_NAME`.
- Provide an email subject and body (job description is optional and will be appended to the body).
- Click "Extract emails" then "Send emails now" (start with Dry run).

### PDF to contacts CSV (if your data comes via PDFs)
```
python pdf_extract_emails.py --pdf path/to/file1.pdf path/to/file2.pdf --out contacts.csv
```
This produces `contacts.csv` with an `email` column (and empty placeholders for other fields).

### Send emails from a CSV
```
python send_mail.py --contacts contacts.csv --out_sent sent_log.csv --dry
```
CSV fields expected for sending: `email`, `job_post_text`, `company`, `post_url`, optional `letter_path`.

#### Sending when contacts came from PDF only
If your `contacts.csv` only has `email`, you can provide a default job post text and/or default company so letters and messages are generated consistently:
```
python send_mail.py --contacts contacts.csv --jobfile_default job_post.txt --company_default "Entreprise" --out_sent sent_log.csv --dry
```
Remove `--dry` to actually send.

## Notes

- PDF files are ignored by Git (`.gitignore`) to avoid pushing personal documents.
- The app sends emails directly without saving any files to disk (no `tmp_uploads/` or `out_letters/`).
- Use responsibly and ensure compliance with laws.
