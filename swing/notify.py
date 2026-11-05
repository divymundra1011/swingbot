import os, smtplib, requests
from email.message import EmailMessage

def telegram(text):
    tok, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat: print("[telegram skipped: no secrets]\n" + text); return
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", json=dict(chat_id=chat, text=text[:4000]), timeout=20)
    print("telegram:", r.status_code)

def email(subject, body, files):
    user, pw, to = os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_APP_PASSWORD"), os.environ.get("MAIL_TO") or os.environ.get("GMAIL_USER")
    if not user or not pw: print("[email skipped: no secrets]"); return
    m = EmailMessage(); m["From"], m["To"], m["Subject"] = user, to, subject; m.set_content(body)
    for f in files:
        m.add_attachment(open(f, "rb").read(), maintype="application", subtype="octet-stream", filename=os.path.basename(f))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s: s.login(user, pw); s.send_message(m)
    print("email sent")
