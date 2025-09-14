from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import random

# ==== CONFIGURATION ====
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
OWNER_ID = 6673230400
FORCE_CHANNELS = ["@Tech_Anish", "@Modinex"]
EMOJIS = ["❤️", "🔥", "👍", "🎉", "😂", "💯", "😍", "👏", "🤩", "😎", "🥳", "💖"]

# ==== USER DATA (RAM ONLY, RESET EVERY DEPLOY) ====
user_db = set()

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
    """User must be joined to all channels in FORCE_CHANNELS"""
    for channel in FORCE_CHANNELS:
        out = telegram_api("getChatMember", {
            "chat_id": channel,
            "user_id": user_id
        })
        print(f"getChatMember {channel} =>", out)
        if not (out.get("ok") and out["result"].get("status") in ["member", "administrator", "creator"]):
            return False
    return True

def send_msg(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    res = telegram_api("sendMessage", data)
    print("Sent message:", res)
    return res

def handle_start(update):
    msg = update["message"]
    user = msg["from"]
    chat = msg["chat"]
    print("/start from", user["id"])

    # Save new user for broadcast
    if chat["type"] == "private":
        user_db.add(chat["id"])

    # Force join logic
    if not check_all_channels_joined(user["id"]):
        buttons = [
            [{"text": "📢 Join Channel 1", "url": "https://t.me/Tech_Anish"}],
            [{"text": "📢 Join Channel 2", "url": "https://t.me/Modinex"}],
            [{"text": "✅ Check Again", "callback_data": "check_joined"}]
        ]
        markup = {"inline_keyboard": buttons}
        send_msg(chat["id"], "⚠️ To use this bot, join all channels below:", markup)
        return

    # Get bot username for Add to Group
    bot_info = telegram_api("getMe")
    bot_username = bot_info.get("result", {}).get("username", "")
    welcome_text = f"👋 Welcome {user.get('first_name','')}!\n\n🤖 Group Manager Bot\n\n✨ Features:\n• Auto reactions\n• Welcome messages\n• Broadcast system"
    markup = {"inline_keyboard": [
        [{"text": "➕ Add to Group", "url": f"https://t.me/{bot_username}?startgroup=true"}]
    ]}
    send_msg(chat["id"], welcome_text, markup)

def handle_callback(update):
    query = update["callback_query"]
    user_id = query["from"]["id"]
    print("Callback:", query)

    # Always answer callback query
    telegram_api("answerCallbackQuery", {"callback_query_id": query["id"]})

    if query["data"] != "check_joined":
        return
    joined = check_all_channels_joined(user_id)

    text = "✅ Thank you for joining! Now you can use the bot." if joined else "❌ Please join all channels first, then tap again."
    telegram_api("editMessageText", {
        "chat_id": query["message"]["chat"]["id"],
        "message_id": query["message"]["message_id"],
        "text": text
    })
    if joined:
        user_db.add(user_id)

def handle_new_member(update):
    msg = update["message"]
    for member in msg.get("new_chat_members", []):
        if not member.get("is_bot", False):
            bot_info = telegram_api("getMe")
            bot_username = bot_info.get("result", {}).get("username", "")
            markup = {"inline_keyboard": [
                [{"text": "➕ Add to Group", "url": f"https://t.me/{bot_username}?startgroup=true"}]
            ]}
            send_msg(msg["chat"]["id"], f"👋 Welcome {member['first_name']}!", markup)

def handle_channel_post(update):
    post = update["channel_post"]
    print("Channel post received:", post)
    # Only react if bot is admin and can see
    emoji = random.choice(EMOJIS)
    result = telegram_api("setMessageReaction", {
        "chat_id": post["chat"]["id"],
        "message_id": post["message_id"],
        "reaction": [{"type": "emoji", "emoji": emoji}]
    })
    print("Set reaction:", result)

def handle_broadcast(update):
    msg = update["message"]
    user_id = msg["from"]["id"]
    if user_id != OWNER_ID:
        send_msg(msg["chat"]["id"], "❌ Not authorized for broadcast")
        return
    args = msg.get("text", "").split(" ",1)
    if len(args) < 2 or not args[1].strip():
        send_msg(msg["chat"]["id"], "⚠️ Usage: /broadcast your message here")
        return
    bc_text = args[1]
    sent = 0
    for uid in user_db:
        try:
            telegram_api("sendMessage", {"chat_id": uid, "text": f"📢 Broadcast:\n\n{bc_text}"})
            sent += 1
        except: pass
    send_msg(msg["chat"]["id"], f"✅ Broadcast sent to {sent} users")

def process_update(update):
    print("Received update:", update)
    # Main logic
    if "message" in update:
        msg = update["message"]
        if "text" in msg and msg["text"].startswith("/start"):
            handle_start(update)
        elif "text" in msg and msg["text"].startswith("/broadcast"):
            handle_broadcast(update)
        elif "new_chat_members" in msg:
            handle_new_member(update)
    elif "callback_query" in update:
        handle_callback(update)
    elif "channel_post" in update:
        handle_channel_post(update)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "🤖 Bot is running!", "ok": True}).encode())
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
