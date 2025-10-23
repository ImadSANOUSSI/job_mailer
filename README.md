# Job Mailer

## Overview

- **Script A (`modify_letter.py`)**: Personalizes a French cover letter from a `.docx` template using an LLM, based on a job post text, and saves a new `.docx`.
- **Script B (`linkedin_scraper.py`)**: Collects emails related to LinkedIn posts via the preferred LinkedIn API approach, with a Selenium fallback. (Optional)
- **Script C (`send_mail.py`)**: Generates tailored email subject/body per contact, attaches your CV and the generated letter, and sends via SMTP.
- **Script D (`pdf_extract_emails.py`)**: Extracts emails from one or more PDFs and writes a `contacts.csv` compatible with `send_mail.py`.
 - **Streamlit App (`streamlit_app.py`)**: Web UI to upload PDFs/DOCX or URLs, extract and filter emails by field, upload CV and template, enter SMTP creds, and send emails.

## Legal and Ethical Notes

- **LinkedIn**: Automated scraping may violate Terms of Service and laws. Prefer the official LinkedIn API with proper permissions.
- **Email**: Comply with anti-spam laws. Only contact addresses you are allowed to, include an opt-out, and respect consent.
- **Security**: Use environment variables for credentials. Do not hard-code secrets.

## Project Layout

```
job-mailer/
├─ README.md
├─ requirements.txt
├─ templates/
│  └─ lettre_template.docx
│  └─ cv.pdf
├─ modify_letter.py
├─ linkedin_scraper.py
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
- Upload PDFs/DOCX and/or paste URLs.
- Choose field (Data/AI, Cybersecurity, Dev) and optional extra keywords.
- Upload your CV (PDF) and template (PDF).
- Enter `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_NAME`.
- Provide an email subject and body (job description is optional and will be appended to the body).
- Click "Extract emails" then "Send emails now" (start with Dry run).

### PDF to contacts CSV (recommended if your data comes via PDFs):
```
python pdf_extract_emails.py --pdf path/to/file1.pdf path/to/file2.pdf --out contacts.csv
```
This produces `contacts.csv` with an `email` column (and empty placeholders for other fields).

- Generate a personalized letter:
```
python modify_letter.py --jobfile path/to/job_post.txt --out out_folder
```

- Fetch contacts (API mode or Selenium fallback):
```
python linkedin_scraper.py --mode api --query "your search"
python linkedin_scraper.py --mode selenium --input urls.csv --out contacts.csv
```

- Send emails from a CSV:
```
python send_mail.py --contacts contacts.csv --out_sent sent_log.csv --dry
```

CSV fields expected for sending: `email`, `job_post_text`, `company`, `post_url`, optional `letter_path`.

### Sending when contacts came from PDF only

If your `contacts.csv` only has `email`, you can provide a default job post text and/or default company so letters and messages are generated consistently:

```
python send_mail.py --contacts contacts.csv --jobfile_default job_post.txt --company_default "Entreprise" --out_sent sent_log.csv --dry
```
Remove `--dry` to actually send.
