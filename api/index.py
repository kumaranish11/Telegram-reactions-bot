from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import random

# Bot Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
OWNER_ID = 6673230400
FORCE_CHANNELS = ["@Tech_Anish", "@Modinex"]
EMOJIS = ["❤️", "🔥", "👍", "🎉", "😂", "💯", "😍", "👏", "🤩", "😎", "🥳", "💖"]

# Simple user storage (in production use database)
user_db = set()

def send_telegram_request(method, data=None):
    """Helper function to send requests to Telegram API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if data:
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        return response.json()
    except:
        return {"ok": False}

def check_channel_membership(user_id):
    """Check if user joined force channels"""
    for channel in FORCE_CHANNELS:
        try:
            result = send_telegram_request(f"getChatMember", {
                "chat_id": channel,
                "user_id": user_id
            })
            if result.get("ok") and result["result"]["status"] in ["left", "kicked"]:
                return False
        except:
            return False
    return True

def send_message(chat_id, text, reply_markup=None):
    """Send message to Telegram"""
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    return send_telegram_request("sendMessage", data)

def handle_start(update):
    """Handle /start command"""
    user = update["message"]["from"]
    chat = update["message"]["chat"]
    
    # Add user to database if private chat
    if chat["type"] == "private":
        user_db.add(chat["id"])
    
    # Check channel membership
    if not check_channel_membership(user["id"]):
        keyboard = {
            "inline_keyboard": [
                [{"text": "📢 Join Channel 1", "url": "https://t.me/Tech_Anish"}],
                [{"text": "📢 Join Channel 2", "url": "https://t.me/Modinex"}],
                [{"text": "✅ Check Again", "callback_data": "check_joined"}]
            ]
        }
        send_message(chat["id"], "⚠️ To use this bot, join channels first:", keyboard)
        return
    
    # Get bot info for group add button
    bot_info = send_telegram_request("getMe")
    bot_username = bot_info.get("result", {}).get("username", "")
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "➕ Add to Group", "url": f"https://t.me/{bot_username}?startgroup=true"}]
        ]
    }
    
    welcome_text = f"👋 Welcome {user['first_name']}!\n\n🤖 **Group Manager Bot**\n\n✨ Features:\n• Auto reactions\n• Welcome messages\n• Broadcast system"
    
    send_message(chat["id"], welcome_text, keyboard)

def handle_callback(update):
    """Handle callback queries"""
    query = update["callback_query"]
    user_id = query["from"]["id"]
    
    if query["data"] == "check_joined":
        # Answer callback query
        send_telegram_request("answerCallbackQuery", {"callback_query_id": query["id"]})
        
        if check_channel_membership(user_id):
            # Edit message
            send_telegram_request("editMessageText", {
                "chat_id": query["message"]["chat"]["id"],
                "message_id": query["message"]["message_id"],
                "text": "✅ Thank you for joining! Now you can use the bot."
            })
            user_db.add(user_id)
        else:
            send_telegram_request("editMessageText", {
                "chat_id": query["message"]["chat"]["id"],
                "message_id": query["message"]["message_id"],
                "text": "❌ Please join all channels first."
            })

def handle_new_member(update):
    """Handle new chat members"""
    message = update["message"]
    if "new_chat_members" in message:
        for member in message["new_chat_members"]:
            if not member.get("is_bot", False):
                bot_info = send_telegram_request("getMe")
                bot_username = bot_info.get("result", {}).get("username", "")
                
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "➕ Add to Group", "url": f"https://t.me/{bot_username}?startgroup=true"}]
                    ]
                }
                
                welcome_text = f"👋 Welcome {member['first_name']}!\n\n🤖 Group Manager Bot"
                send_message(message["chat"]["id"], welcome_text, keyboard)

def handle_channel_post(update):
    """Handle channel posts for auto reactions"""
    if "channel_post" in update:
        post = update["channel_post"]
        emoji = random.choice(EMOJIS)
        
        send_telegram_request("setMessageReaction", {
            "chat_id": post["chat"]["id"],
            "message_id": post["message_id"],
            "reaction": [{"type": "emoji", "emoji": emoji}]
        })

def handle_broadcast(update):
    """Handle broadcast command"""
    message = update["message"]
    user_id = message["from"]["id"]
    
    if user_id != OWNER_ID:
        send_message(message["chat"]["id"], "❌ Not authorized")
        return
    
    # Get broadcast message
    text_parts = message["text"].split(" ", 1)
    if len(text_parts) < 2:
        send_message(message["chat"]["id"], "⚠️ Usage: /broadcast Your message here")
        return
    
    broadcast_text = text_parts[1]
    success_count = 0
    
    for user_id in user_db:
        try:
            result = send_message(user_id, f"📢 Broadcast:\n\n{broadcast_text}")
            if result.get("ok"):
                success_count += 1
        except:
            continue
    
    send_message(message["chat"]["id"], f"✅ Broadcast sent to {success_count} users")

def process_update(update):
    """Process incoming webhook update"""
    try:
        # Handle different types of updates
        if "message" in update:
            message = update["message"]
            
            # Handle commands
            if "text" in message and message["text"].startswith("/"):
                command = message["text"].split(" ")[0]
                if command == "/start":
                    handle_start(update)
                elif command == "/broadcast":
                    handle_broadcast(update)
            
            # Handle new chat members
            elif "new_chat_members" in message:
                handle_new_member(update)
        
        # Handle callback queries
        elif "callback_query" in update:
            handle_callback(update)
        
        # Handle channel posts
        elif "channel_post" in update:
            handle_channel_post(update)
            
    except Exception as e:
        print(f"Error processing update: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {"status": "🤖 Bot is running!", "ok": True}
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Handle POST requests (webhook)"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON data
            update = json.loads(post_data.decode('utf-8'))
            
            # Process the update
            process_update(update)
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {"ok": True}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Webhook error: {e}")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {"ok": False, "error": str(e)}
            self.wfile.write(json.dumps(response).encode())

