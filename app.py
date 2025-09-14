from flask import Flask, request, jsonify
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import random
import asyncio

app = Flask(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = 6673230400
FORCE_CHANNELS = ["@Tech_Anish", "@Modinex"]
EMOJIS = ["❤️", "🔥", "👍", "🎉", "😂", "💯", "😍", "👏", "🤩", "😎", "🥳", "💖"]

user_db = set()
bot = Bot(BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

async def check_join(update, context):
    user_id = update.effective_user.id
    for channel in FORCE_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                keyboard = [
                    [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/Tech_Anish")],
                    [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/Modinex")],
                    [InlineKeyboardButton("✅ Check Again", callback_data="check_joined")]
                ]
                await update.message.reply_text("⚠️ Join channels first:", reply_markup=InlineKeyboardMarkup(keyboard))
                return False
        except:
            pass
    return True

async def start(update, context):
    if update.effective_chat.type == 'private':
        user_db.add(update.effective_chat.id)
    
    if not await check_join(update, context):
        return
    
    bot_info = await context.bot.get_me()
    keyboard = [[InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_info.username}?startgroup=true")]]
    
    await update.message.reply_text(
        f"👋 Welcome {update.effective_user.first_name}!\n\n🤖 Group Manager Bot\n\n✨ Features:\n• Auto reactions\n• Welcome messages\n• Broadcast system",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def new_member(update, context):
    for member in update.message.new_chat_members:
        if not member.is_bot:
            bot_info = await context.bot.get_me()
            keyboard = [[InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_info.username}?startgroup=true")]]
            await update.message.reply_text(f"👋 Welcome {member.first_name}!", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    joined = True
    for channel in FORCE_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                joined = False
                break
        except:
            joined = False
            break
    
    if joined:
        await query.edit_message_text("✅ Thanks! Now you can use the bot.")
        user_db.add(user_id)
    else:
        await query.edit_message_text("❌ Please join channels first.")

async def channel_react(update, context):
    if update.channel_post:
        emoji = random.choice(EMOJIS)
        try:
            await context.bot.set_message_reaction(
                chat_id=update.channel_post.chat.id,
                message_id=update.channel_post.message_id,
                reaction=[{"type": "emoji", "emoji": emoji}]
            )
        except:
            pass

async def broadcast(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Not authorized")
        return
    
    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text("⚠️ Provide message: /broadcast Your message")
        return
    
    count = 0
    for user_id in user_db:
        try:
            await context.bot.send_message(user_id, f"📢 Broadcast:\n\n{message}")
            count += 1
        except:
            pass
    
    await update.message.reply_text(f"✅ Sent to {count} users")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("broadcast", broadcast))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
application.add_handler(CallbackQueryHandler(check_callback, pattern="check_joined"))
application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, channel_react))

@app.route('/')
def home():
    return jsonify({"status": "Bot Running! 🤖"})

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        if json_data:
            update = Update.de_json(json_data, bot)
            asyncio.run(application.process_update(update))
        return jsonify({"ok": True})
    except:
        return jsonify({"error": "Failed"}), 500

if __name__ == '__main__':
    app.run()
