import json
import os
import requests

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
FORCE_CHANNELS = ["@Tech_Anish", "@Modinex"]

def main(request):
    # Main Vercel handler function
    try:
        if request.method == "GET":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"status": "Bot working!", "ok": True})
            }
        elif request.method == "POST":
            # This receives telegram webhook update!
            payload = request.get_json()
            print("WEBHOOK UPDATE:", json.dumps(payload))
            # Minimal reply (Bot will simply send a message back to sender for every chat message)
            if "message" in payload and "text" in payload["message"]:
                msg = payload["message"]
                chat_id = msg["chat"]["id"]
                text = msg["text"]
                # Reply with debug
                send_msg(chat_id, f"Debug Reply: You sent '{text}'")
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"ok": True})
            }
        else:
            return {"statusCode": 405, "body": "Method Not Allowed"}
    except Exception as e:
        print("Handler exception:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def send_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, json=data, timeout=10)
        print("SendMessage to chat", chat_id, "result:", r.text)
    except Exception as e:
        print("SendMessage error:", e)
