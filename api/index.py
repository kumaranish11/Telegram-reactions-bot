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

def process_update(update):
    print("🚩 UPDATE BODY:", json.dumps(update))
    if "message" in update and "text" in update["message"]:
        msg = update["message"]
        uid = msg["from"]["id"]
        print("User id:", uid, "| Message:", msg["text"])
        telegram_api("sendMessage", {"chat_id": msg["chat"]["id"], "text": "Debug OK: Got your message!"})

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
            print("RAW POST BODY:", post_data)
            try:
                update = json.loads(post_data.decode('utf-8'))
            except Exception as e:
                print("JSON ERROR:", e)
                update = {}
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
