import os
import imaplib
import email
import requests
import json
from email.header import decode_header
from flask import Flask, jsonify, render_template # <-- 1. IMPORT RENDER_TEMPLATE

SELECTED_MODEL = "gemma:2b"
app = Flask(__name__)

# Load credentials from environment variables
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')

# Ollama API endpoint
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://ollama:11434/api/generate')

def summarize_text(text_to_summarize):
    """Sends text to the Ollama API for summarization."""
    if not text_to_summarize.strip():
        return "Email body was empty, no summary generated."
    
    try:
        payload = {
            "model": SELECTED_MODEL,  # <-- Use the model you pulled in setup_ollama.sh
            "prompt": f"Please provide a concise, one-paragraph summary of the following email text:\n\n---\n\n{text_to_summarize}",
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "No summary found in response.").strip()

    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
        return f"Could not summarize: {e}"
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from Ollama response: {response.text}")
        return "Could not summarize: Invalid response from API."


def get_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        latest_email_ids = email_ids[-5:]
        
        email_list = []

        for e_id in reversed(latest_email_ids):
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    from_ = msg.get("From")
                    email_data = {"subject": subject, "from": from_, "body": ""}

                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode()
                                    email_data["body"] = body
                                    break
                                except:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode()
                            email_data["body"] = body
                        except:
                            pass
                            
                    email_list.append(email_data)

        mail.logout()
        return email_list

    except Exception as e:
        print(f"Error connecting to Gmail: {e}")
        return {"error": str(e)}

# 2. ADD THIS NEW ROUTE TO SERVE THE FRONTEND
@app.route('/')
def home():
    """Serves the main HTML page."""
    return render_template('index.html')


@app.route('/summarize-emails')
def summarize_emails_route():
    """This is now our backend API endpoint for the frontend to call."""
    emails = get_emails()
    if "error" in emails:
        return jsonify(emails), 500
    
    for mail in emails:
        summary = summarize_text(mail['body'])
        mail['summary'] = summary

    return jsonify(emails)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)