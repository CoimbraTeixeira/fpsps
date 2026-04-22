import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RECIPIENT = "rot@pobox.com"


def send_notification(alerts: list[dict]):
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]

    airline_names = ", ".join(a["airline"] for a in alerts)
    subject = f"[fpsps] Points promotion detected: {airline_names}"

    html_sections = []
    for alert in alerts:
        promos = alert.get("promotions", [])
        if promos:
            items = "".join(f"<li>{p}</li>" for p in promos)
            promo_block = f"<ul>{items}</ul>"
        else:
            promo_block = "<p>Page content changed — check the link above for details.</p>"

        html_sections.append(f"""
            <div style="margin-bottom:24px;border-left:4px solid #0057b8;padding-left:12px">
                <h2 style="margin:0 0 4px">{alert["airline"]}</h2>
                <p style="margin:0 0 8px">
                    <a href="{alert["url"]}">{alert["url"]}</a>
                </p>
                {promo_block}
            </div>
        """)

    html_body = f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:auto;color:#222">
        <h1 style="border-bottom:1px solid #ddd;padding-bottom:8px">
            ✈ Flight Points Promotion Alert
        </h1>
        {"".join(html_sections)}
        <p style="color:#888;font-size:12px;margin-top:32px">
            Monitored by <strong>fpsps</strong> via GitHub Actions
        </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_password)
        smtp.sendmail(gmail_user, RECIPIENT, msg.as_string())
