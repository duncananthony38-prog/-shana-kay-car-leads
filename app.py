import os
import csv
import secrets
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DEALERSHIP_NAME = os.getenv("DEALERSHIP_NAME", "Ken Ganley CDJR Bedford")
DEALERSHIP_URL = os.getenv("DEALERSHIP_URL", "https://www.kenganleycdjrbedford.com/")
AGENT_NAME = os.getenv("AGENT_NAME", "Shana-Kay Gardener")
AGENT_PHONE = os.getenv("AGENT_PHONE", "+18482989384")
AGENT_PHONE_DISPLAY = os.getenv("AGENT_PHONE_DISPLAY", "+1 (848) 298-9384")
AGENT_EMAIL = os.getenv("AGENT_EMAIL", "Sgardener@ganleyauto.com")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-5522461054")
LEADS_FILE = Path("leads.csv")

def make_lead_id():
    stamp = datetime.now().strftime("%y%m%d%H%M")
    suffix = secrets.token_hex(2).upper()
    return f"KG-{stamp}-{suffix}"

def log_lead(row):
    is_new = not LEADS_FILE.exists()
    with LEADS_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "lead_id", "timestamp", "name", "phone", "email",
                "vehicle", "contact_method", "source", "notes"
            ],
        )
        if is_new:
            writer.writeheader()
        writer.writerow(row)

def send_telegram(row):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False, "Telegram is not configured."

    text = (
        "🚗 NEW CAR LEAD\n\n"
        f"Lead ID: {row['lead_id']}\n"
        f"Sales Agent: {AGENT_NAME}\n"
        f"Name: {row['name']}\n"
        f"Phone: {row['phone']}\n"
        f"Email: {row['email'] or 'Not provided'}\n"
        f"Vehicle: {row['vehicle'] or 'Not specified'}\n"
        f"Preferred contact: {row['contact_method']}\n"
        f"Source: {row['source']}\n"
        f"Notes: {row['notes'] or 'None'}\n"
        f"Time: {row['timestamp']}"
    )

    endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        endpoint,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        timeout=15,
    )
    return response.ok, response.text

@app.get("/")
def home():
    source = request.args.get("source", "Direct")
    return render_template(
        "index.html",
        dealership_name=DEALERSHIP_NAME,
        dealership_url=DEALERSHIP_URL,
        agent_name=AGENT_NAME,
        agent_phone=AGENT_PHONE,
        agent_phone_display=AGENT_PHONE_DISPLAY,
        agent_email=AGENT_EMAIL,
        source=source,
    )

@app.post("/submit")
def submit():
    if not request.form.get("consent"):
        return "Consent is required before submitting your contact details.", 400

    row = {
        "lead_id": make_lead_id(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": request.form.get("name", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "email": request.form.get("email", "").strip(),
        "vehicle": request.form.get("vehicle", "").strip(),
        "contact_method": request.form.get("contact_method", "Text").strip(),
        "source": request.form.get("source", "Direct").strip(),
        "notes": request.form.get("notes", "").strip(),
    }

    if not row["name"] or not row["phone"]:
        return "Name and phone number are required.", 400

    log_lead(row)
    send_telegram(row)

    return redirect(url_for("thanks", lead_id=row["lead_id"]))

@app.get("/thanks")
def thanks():
    lead_id = request.args.get("lead_id", "")
    return render_template(
        "thanks.html",
        lead_id=lead_id,
        dealership_name=DEALERSHIP_NAME,
        dealership_url=DEALERSHIP_URL,
        agent_name=AGENT_NAME,
        agent_phone=AGENT_PHONE,
        agent_phone_display=AGENT_PHONE_DISPLAY,
        agent_email=AGENT_EMAIL,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
