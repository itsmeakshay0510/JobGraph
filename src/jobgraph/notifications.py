from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

from .models import EmailSettings, TailoredResume


def send_digest_email(email_settings: EmailSettings, generated: list[TailoredResume]) -> None:
    if not email_settings.enabled or not generated:
        return
    password = os.environ.get(email_settings.password_env, "")
    if not password:
        logging.warning(
            "Email delivery skipped because %s is not set.",
            email_settings.password_env,
        )
        return

    subject = f"{len(generated)} tailored resume(s) generated"
    lines = []
    for item in generated:
        lines.extend(
            [
                f"Company: {item.company}",
                f"Role: {item.role}",
                f"Markdown: {item.output_markdown_path}",
                f"DOCX: {item.output_docx_path}",
                "",
            ]
        )
    body = "\n".join(lines).strip()

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = email_settings.from_address or email_settings.username
    message["To"] = ", ".join(email_settings.to_addresses)
    message.set_content(body)

    for item in generated:
        for attachment_path in (item.output_markdown_path, item.output_docx_path):
            if not attachment_path:
                continue
            with attachment_path.open("rb") as handle:
                message.add_attachment(
                    handle.read(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=attachment_path.name,
                )

    try:
        with smtplib.SMTP(email_settings.smtp_host, email_settings.smtp_port) as smtp:
            if email_settings.use_tls:
                smtp.starttls()
            smtp.login(email_settings.username, password)
            smtp.send_message(message)
        logging.info("Email digest sent to %s", ", ".join(email_settings.to_addresses))
    except smtplib.SMTPException as error:
        logging.warning("Email delivery failed: %s", error)
