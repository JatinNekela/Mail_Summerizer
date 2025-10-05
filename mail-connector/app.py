import os
import imaplib
import email
import requests
import json
from email.header import decode_header
from flask import Flask, jsonify, render_template, request

# --- Import the official Cerebras SDK ---
from cerebras.cloud.sdk import Cerebras

app = Flask(__name__, template_folder='templates')

# --- Environment Variables ---
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')

# --- Initialize the Cerebras Client ---
# The SDK is smart and automatically finds the CEREBRAS_API_KEY
# from the environment variables you set in docker-compose.yml.
try:
    client = Cerebras()
except Exception as e:
    print(f"CRITICAL ERROR: Could not initialize Cerebras client. Is CEREBRAS_API_KEY set? Details: {e}")
    client = None

# --- AI Functions using the Cerebras SDK ---

def summarize_text(text_to_summarize, model_name):
    """Creates a summarization prompt and sends it to the Cerebras API via the SDK."""
    if not client:
        return "Cerebras client is not initialized. Check server logs for API key issues."
    if not text_to_summarize.strip():
        return "Email body was empty, no summary generated."

    try:
        prompt = f"Please provide a concise, one-paragraph summary of the following email text:\n\n---\n\n{text_to_summarize}"
        
        # Use the SDK to create a chat completion
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_name,
        )
        # The SDK returns a structured object; we extract the content
        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"Error calling Cerebras API for summary: {e}")
        return f"Could not get summary from AI service: {e}"


def chat_with_email(email_body, question, history, model_name):
    """Creates a chat prompt with history and sends it to the Cerebras API."""
    if not client:
        return "Cerebras client is not initialized. Check server logs for API key issues."

    try:
        # Start with a "system" message to give the AI context and instructions
        messages = [{
            "role": "system",
            "content": f"You are a helpful assistant. Answer questions based on the following email content:\n\n{email_body}"
        }]

        # Add the previous back-and-forth messages from the conversation
        messages.extend(history)

        # Add the new question from the user
        messages.append({"role": "user", "content": question})

        # Call the API with the full conversation context
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_name,
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"Error calling Cerebras API for chat: {e}")
        return f"Could not get chat response from AI service: {e}"


# --- Gmail Helper Functions (No changes needed here) ---

def get_single_email_body(email_id):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        if status != 'OK': return None
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try: body = part.get_payload(decode=True).decode(); break
                            except: continue
                else:
                    try: body = msg.get_payload(decode=True).decode()
                    except: pass
                return body
        mail.logout()
        return ""
    except Exception as e:
        print(f"Error fetching single email: {e}")
        return None

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
                    if isinstance(subject, bytes): subject = subject.decode(encoding if encoding else "utf-8")
                    from_ = msg.get("From")
                    email_data = {"id": e_id.decode(), "subject": subject, "from": from_, "body": ""}
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try: email_data["body"] = part.get_payload(decode=True).decode(); break
                                except: pass
                    else:
                        try: email_data["body"] = msg.get_payload(decode=True).decode()
                        except: pass
                    email_list.append(email_data)
        mail.logout()
        return email_list
    except Exception as e:
        return {"error": str(e)}

# --- Flask Routes (No changes needed here) ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat/<email_id>')
def chat_page(email_id):
    return render_template('chat.html', email_id=email_id)

@app.route('/summarize-emails', methods=['POST'])
def summarize_emails_route():
    data = request.get_json()
    model = data.get('model', 'llama-4-scout-17b-16e-instruct') # Default to a Cerebras model
    emails = get_emails()
    if "error" in emails: return jsonify(emails), 500
    for mail in emails:
        summary = summarize_text(mail['body'], model)
        mail['summary'] = summary
        del mail['body']
    return jsonify(emails)

@app.route('/chat-api', methods=['POST'])
def chat_api():
    data = request.get_json()
    email_id = data.get('email_id')
    question = data.get('question')
    history = data.get('history', [])
    model = data.get('model', 'llama-4-scout-17b-16e-instruct') # Default to a Cerebras model
    if not all([email_id, question, model]): return jsonify({"error": "Missing required data"}), 400
    email_body = get_single_email_body(email_id.encode())
    if email_body is None: return jsonify({"error": "Could not retrieve email"}), 404
    answer = chat_with_email(email_body, question, history, model)
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

