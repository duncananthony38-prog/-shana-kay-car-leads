import os
import csv
import secrets
from datetime import datetime

import requests
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

DEALERSHIP_NAME = "Ken Ganley CDJR Bedford"
DEALERSHIP_URL = "https://www.kenganleycdjrbedford.com/"
AGENT_NAME = "Shana-Kay Gardener"
AGENT_PHONE = "+18482989384"
AGENT_PHONE_DISPLAY = "+1 (848) 298-9384"
AGENT_EMAIL = "Sgardener@ganleyauto.com"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-5522461054")

HOME_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ agent_name }} | {{ dealership_name }}</title>
<style>
body{margin:0;font-family:Arial,sans-serif;background:#0b0d10;color:#f5f7fa}
.container{max-width:850px;margin:auto;padding:35px 20px 70px}
.badge{display:inline-block;color:#ffb000;border:1px solid #333;border-radius:20px;padding:8px 12px}
h1{font-size:46px;margin-bottom:12px}
.subtitle{color:#b5bec9;font-size:18px;line-height:1.6}
.agent{background:#15191e;padding:18px;border-radius:15px;margin:25px 0}
.buttons{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}
.btn{text-decoration:none;color:white;background:#252b32;padding:14px 18px;border-radius:10px;font-weight:bold}
.primary{background:#ffb000;color:#111}
.card{background:#15191e;border-radius:18px;padding:25px;margin-top:35px}
label{display:block;margin-top:15px;margin-bottom:6px;font-weight:bold}
input,select,textarea{width:100%;box-sizing:border-box;padding:14px;border-radius:9px;border:1px solid #343b44;background:#0f1317;color:white;font-size:16px}
button{width:100%;margin-top:20px;padding:16px;border:0;border-radius:10px;background:#ffb000;color:#111;font-size:17px;font-weight:bold}
.consent{display:flex;gap:10px;margin-top:18px;color:#b5bec9}
.consent input{width:auto}
.small{color:#8f99a5;font-size:13px;margin-top:18px}
@media(max-width:600px){h1{font-size:38px}.buttons{flex-direction:column}}
</style>
</head>
<body>
<div class="container">
<div class="badge">Ken Ganley CDJR Bedford Sales</div>
<h1>Shop with {{ agent_name }}</h1>
<p class="subtitle">Looking for a Chrysler, Dodge, Jeep or Ram? Send your request directly to {{ agent_name }} and get help finding the right vehicle.</p>

<div class="agent">
<strong>{{ agent_name }}</strong><br>
{{ agent_phone_display }}<br>
{{ agent_email }}
</div>

<div class="buttons">
<a class="btn" href="tel:{{ agent_phone }}">Call Shana-Kay</a>
<a class="btn" href="sms:{{ agent_phone }}">Text Shana-Kay</a>
<a class="btn" href="mailto:{{ agent_email }}">Email Shana-Kay</a>
<a class="btn primary" href="{{ dealership_url }}" target="_blank" rel="noopener">Browse Vehicles</a>
</div>

<div class="card">
<h2>Tell Shana-Kay what you're looking for</h2>

<form method="post" action="/submit">
<input type="hidden" name="source" value="{{ source }}">

<label>Full name</label>
<input name="name" required>

<label>Phone number</label>
<input name="phone" required>

<label>Email</label>
<input name="email" type="email">

<label>Vehicle you're interested in</label>
<input name="vehicle" placeholder="Example: Jeep Grand Cherokee">

<label>Preferred contact method</label>
<select name="contact_method">
<option>Text</option>
<option>Phone call</option>
<option>Email</option>
</select>

<label>Notes</label>
<textarea name="notes" rows="4" placeholder="Budget, trade-in, appointment time, etc."></textarea>

<div class="consent">
<input type="checkbox" name="consent" required>
<span>I agree that Shana-Kay Gardener and/or the dealership may contact me about my vehicle inquiry.</span>
</div>

<button type="submit">Send request to Shana-Kay</button>
</form>

<p class="small">Your information is submitted voluntarily for this vehicle inquiry.</p>
</div>
</div>
</body>
</html>
"""

THANKS_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lead Sent</title>
<style>
body{background:#0b0d10;color:white;font-family:Arial,sans-serif;text-align:center;padding:60px 20px}
.card{max-width:600px;margin:auto;background:#15191e;padding:35px;border-radius:18px}
.check{font-size:60px;color:#ffb000}
a{display:inline-block;margin-top:15px;padding:14px 18px;border-radius:10px;background:#ffb000;color:#111;text-decoration:none;font-weight:bold}
</style>
</head>
<body>
<div class="card">
<div class="check">✓</div>
<h1>Your request was sent!</h1>
<p>Shana-Kay Gardener can follow up using the contact information you submitted.</p>
<p>Lead ID: <strong>{{ lead_id }}</strong></p>
<a href="{{ dealership_url }}" target="_blank" rel="noopener">Browse Vehicles</a>
</div>
</body>
</html>
"""

def make_lead_id():
    stamp = datetime.now().strftime("%y%m%d%H%M")
    suffix = secrets.token_hex(2).upper()
    return f"KG-{stamp}-{suffix}"

def save_lead(row):
    file_exists = os.path.exists("leads.csv")
    with open("leads.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def send_telegram(row):
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram bot token missing")
        return

    message = (
        "🚗 NEW CAR LEAD\n\n"
        f"Lead ID: {row['lead_id']}\n"
        f"Sales Agent: {AGENT_NAME}\n"
        f"Name: {row['name']}\n"
        f"Phone: {row['phone']}\n"
        f"Email: {row['email'] or 'Not provided'}\n"
        f"Vehicle: {row['vehicle'] or 'Not specified'}\n"
        f"Preferred contact: {row['contact_method']}\n"
        f"Source: {row['source']}\n"
        f"Notes: {row['notes'] or 'None'}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
        timeout=15,
    )
    print("Telegram:", response.status_code, response.text)

@app.route("/")
def home():
    return render_template_string(
        HOME_HTML,
        agent_name=AGENT_NAME,
        agent_phone=AGENT_PHONE,
        agent_phone_display=AGENT_PHONE_DISPLAY,
        agent_email=AGENT_EMAIL,
        dealership_name=DEALERSHIP_NAME,
        dealership_url=DEALERSHIP_URL,
        source=request.args.get("source", "Direct"),
    )

@app.route("/submit", methods=["POST"])
def submit():
    if not request.form.get("consent"):
        return "Consent required", 400

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()

    if not name or not phone:
        return "Name and phone required", 400

    row = {
        "lead_id": make_lead_id(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": name,
        "phone": phone,
        "email": request.form.get("email", "").strip(),
        "vehicle": request.form.get("vehicle", "").strip(),
        "contact_method": request.form.get("contact_method", "Text"),
        "source": request.form.get("source", "Direct"),
        "notes": request.form.get("notes", "").strip(),
    }

    save_lead(row)

    try:
        send_telegram(row)
    except Exception as e:
        print("Telegram error:", e)

    return redirect(url_for("thanks", lead_id=row["lead_id"]))

@app.route("/thanks")
def thanks():
    return render_template_string(
        THANKS_HTML,
        lead_id=request.args.get("lead_id", ""),
        dealership_url=DEALERSHIP_URL,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
