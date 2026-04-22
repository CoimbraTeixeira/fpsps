import json
import os
import urllib.request

RECIPIENT = "rot@pobox.com"
FROM = "fpsps <onboarding@resend.dev>"


def send_notification(alerts: list[dict]):
    api_key = os.environ["RESEND_API_KEY"]

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

    payload = json.dumps({
        "from": FROM,
        "to": [RECIPIENT],
        "subject": subject,
        "html": html_body,
    }).encode()

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        print(f"  Email sent, id={result.get('id')}", flush=True)
