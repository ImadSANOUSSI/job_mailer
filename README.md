# Job Mailer

## Overview

- **Script A (`modify_letter.py`)**: Personalizes a French cover letter from a `.docx` template using an LLM, based on a job post text, and saves a new `.docx`.
- **Script B (`linkedin_scraper.py`)**: Collects emails related to LinkedIn posts via the preferred LinkedIn API approach, with a Selenium fallback.
- **Script C (`send_mail.py`)**: Generates tailored email subject/body per contact, attaches your CV and the generated letter, and sends via SMTP.

## Legal and Ethical Notes

- **LinkedIn**: Automated scraping may violate Terms of Service and laws. Prefer the official LinkedIn API with proper permissions.
- **Email**: Comply with anti-spam laws. Only contact addresses you are allowed to, include an opt-out, and respect consent.
- **Security**: Use environment variables for credentials. Do not hard-code secrets.

## Project Layout

```
job-mailer/
├─ README.md
├─ requirements.txt
├─ config.example.env
├─ templates/
│  └─ lettre_template.docx
│  └─ cv.pdf
├─ modify_letter.py
├─ linkedin_scraper.py
├─ send_mail.py
└─ utils.py
```

## Setup

```
python -m venv venv
venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
copy config.example.env .env
```

Fill `.env` with your values.

## Environment Variables

- `OPENAI_API_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_NAME`
- `CV_PATH`, `TEMPLATE_PATH`
- `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REDIRECT_URI`

## Usage

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
