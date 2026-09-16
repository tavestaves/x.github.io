# backend/main.py
import json
import os
import time
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import smtplib

app = FastAPI(title="Panenyasha Teverah Portfolio API", version="2.0.0")

# Enable CORS for local dev and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MESSAGES_FILE = os.path.join(os.path.dirname(__file__), "messages.json")

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    category: Optional[str] = "general"
    message: str

def save_message_fallback(data: dict):
    """Saves incoming messages locally so no inquiry is ever lost."""
    messages = []
    if os.path.exists(MESSAGES_FILE):
        try:
            with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
                messages = json.load(f)
        except Exception:
            messages = []

    data["timestamp"] = datetime.utcnow().isoformat()
    messages.append(data)

    with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)

@app.get("/")
async def root():
    return {
        "system": "Panenyasha Teverah Embedded Portfolio API",
        "status": "ONLINE",
        "version": "2.0.0"
    }

@app.post("/contact")
async def contact(
    name: str = Form(...),
    email: str = Form(...),
    category: str = Form("general"),
    message: str = Form(...)
):
    if not name.strip() or not email.strip() or not message.strip():
        raise HTTPException(status_code=400, detail="Name, email, and message fields are required.")

    message_data = {
        "name": name.strip(),
        "email": email.strip(),
        "category": category.strip(),
        "message": message.strip()
    }

    # Always save to fallback JSON first
    save_message_fallback(message_data)

    # Attempt SMTP if configured in environment
    sender_email = os.getenv("SMTP_SENDER_EMAIL")
    sender_password = os.getenv("SMTP_SENDER_PASSWORD")
    receiver_email = os.getenv("SMTP_RECEIVER_EMAIL", "mrteverah@gmail.com")

    if sender_email and sender_password:
        subject = f"Portfolio Message: [{category}] from {name}"
        body = f"From: {name} ({email})\nCategory: {category}\n\nMessage:\n{message}"
        email_text = f"Subject: {subject}\n\n{body}"

        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=5)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, email_text)
            server.quit()
            return {"status": "success", "message": "Email sent and message saved successfully!"}
        except Exception as e:
            # Saved locally, return success with notice
            return {
                "status": "success",
                "message": "Message saved locally! (SMTP offline)",
                "note": str(e)
            }

    return {
        "status": "success",
        "message": "Message logged successfully into local embedded queue."
    }
