import os
import argparse
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Any
from utils import get_env, get_openai_client, logger, read_csv, write_csv, validate_email
from modify_letter import generate_for_post


def gen_subject_body(job_post_text: str, company: str) -> Dict[str, str]:
    job_post_text = (job_post_text or "").strip()
    if not job_post_text:
        subject = f"Candidature – {company}" if company else "Candidature"
        body = (
            "Bonjour,\n\n"
            "Je vous contacte pour vous proposer ma candidature. Vous trouverez ci-joint mon CV ainsi qu’une lettre de motivation.\n\n"
            "Je reste à votre disposition pour tout échange.\n\n"
            "Cordialement,\n"
        )
        return {"subject": subject[:150], "body": body}
    client = get_openai_client()
    system = (
        "Tu es un assistant qui rédige des emails de candidature concis en français. "
        "Crée un objet et un corps adaptés au poste et à l'entreprise."
    )
    user = (
        f"Entreprise: {company}\n\n"
        f"Description du poste:\n{job_post_text}\n\n"
        "Consignes: objet court et percutant; corps poli, professionnel, avec appel à l'action."
    )
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.4,
        max_tokens=500,
    )
    txt = (r.choices[0].message.content or "").strip()
    lines = [x.strip() for x in txt.splitlines() if x.strip()]
    subject = lines[0][:150] if lines else "Candidature"
    body = "\n".join(lines[1:]) if len(lines) > 1 else txt
    return {"subject": subject, "body": body}


def send_email(smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str, from_name: str, to_addr: str, subject: str, body: str, attachments: List[str]) -> None:
    msg = EmailMessage()
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    for path in attachments:
        if not path or not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(path)[1].lower()
        maintype, subtype = ("application", "octet-stream")
        if ext == ".pdf":
            maintype, subtype = ("application", "pdf")
        elif ext == ".docx":
            maintype, subtype = ("application", "vnd.openxmlformats-officedocument.wordprocessingml.document")
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=os.path.basename(path))
    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)


def main() -> None:
    p = argparse.ArgumentParser(description="Send tailored application emails with attachments.")
    p.add_argument("--contacts", required=True)
    p.add_argument("--out_sent", default="sent_log.csv")
    p.add_argument("--dry", action="store_true")
    p.add_argument("--letters_out", default="out_letters")
    p.add_argument("--jobfile_default", default="", help="Path to a job post text used when a row lacks job_post_text")
    p.add_argument("--company_default", default="", help="Default company name when missing in rows")
    a = p.parse_args()

    smtp_host = get_env("SMTP_HOST", required=True)
    smtp_port = int(get_env("SMTP_PORT", "587"))
    smtp_user = get_env("SMTP_USER", required=True)
    smtp_pass = get_env("SMTP_PASS", required=True)
    from_name = get_env("FROM_NAME", "Candidate")
    cv_path = get_env("CV_PATH", required=True)

    rows = read_csv(a.contacts)
    sent_log: List[Dict[str, Any]] = []

    default_job_text = ""
    if a.jobfile_default:
        try:
            with open(a.jobfile_default, encoding="utf-8") as f:
                default_job_text = f.read().strip()
        except Exception as ex:
            logger.error(f"Failed to read --jobfile_default: {ex}")

    for r in rows:
        email = (r.get("email") or "").strip()
        if not validate_email(email):
            logger.warning(f"Skipping invalid email: {email}")
            continue
        company = (r.get("company") or "").strip() or a.company_default or "Entreprise"
        job_post_text = (r.get("job_post_text") or "").strip() or default_job_text
        letter_path = (r.get("letter_path") or "").strip()
        if not letter_path:
            if job_post_text:
                os.makedirs(a.letters_out, exist_ok=True)
                letter_path = generate_for_post(job_post_text, a.letters_out, f"lettre_{company}")
            else:
                logger.warning(f"No letter_path or job_post_text for {email}")
                continue
        sb = gen_subject_body(job_post_text, company)
        attachments = [cv_path, letter_path]
        if a.dry:
            logger.info(f"DRY RUN -> To: {email} | Subject: {sb['subject']} | Attachments: {attachments}")
        else:
            try:
                send_email(smtp_host, smtp_port, smtp_user, smtp_pass, from_name, email, sb["subject"], sb["body"], attachments)
                sent_log.append({"email": email, "company": company, "letter_path": letter_path, "status": "sent"})
                logger.info(f"Sent to {email}")
            except Exception as ex:
                sent_log.append({"email": email, "company": company, "letter_path": letter_path, "status": f"error: {ex}"})
                logger.error(f"Error sending to {email}: {ex}")

    if sent_log:
        write_csv(a.out_sent, sent_log)
        logger.info(f"Wrote log: {a.out_sent}")


if __name__ == "__main__":
    main()
