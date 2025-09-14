from http.server import BaseHTTPRequestHandler
import json
import os
import requests

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
FORCE_CHANNELS = ["@Tech_Anish", "@Modinex"]

def telegram_api(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if data:
            r = requests.post(url, json=data, timeout=10)
        else:
            r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        print("telegram_api error:", e)
        return {"ok": False}

def check_all_channels_joined(user_id):
    for channel in FORCE_CHANNELS:
        out = telegram_api("getChatMember", {
            "chat_id": channel,
            "user_id": user_id
        })
        print(f"check channel {channel} =>", out)
        if not (out.get("ok") and out["result"].get("status") in ["member", "administrator", "creator"]):
            return False
    return True

def send_msg(chat_id, text):
    data = {"chat_id": chat_id, "text": text}
    res = telegram_api("sendMessage", data)
    print("sendMessage result:", res)
    return res

def process_update(update):
    print("🚩 Telegram update received:", json.dumps(update))
    # Only /start for now!
    if "message" in update and "text" in update["message"]:
        msg = update["message"]
        uid = msg["from"]["id"]
        if msg["text"].startswith("/start"):
            # Force join check!
            if not check_all_channels_joined(uid):
                send_msg(msg["chat"]["id"], "🔴 Please join all required channels first.")
            else:
                send_msg(msg["chat"]["id"], "🟢 Joined! Full bot access granted.")
        else:
            send_msg(msg["chat"]["id"], "This is a debug reply.")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "Bot working!", "ok": True}).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            update = json.loads(post_data.decode('utf-8'))
            process_update(update)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
        except Exception as e:
            print("Webhook error:", e)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
