import logging
import json
import random
import os
import tempfile
import time
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue
from telegram.error import BadRequest, TelegramError
from telegram import InlineQueryResultArticle, InputTextMessageContent
import uuid

# Configuration
BOT_TOKEN = "7993719241:AAE6ItGn4ciaJv8c_Hjwlt01lTqhuqj9j8Q"
CHANNEL_USERNAME = "@megasaruku0"
ADMIN_ID = 1134468682

DATA_FILE = "users_data.json"
ITEMS_FILE = "items.json"

# Initialize bot and logger
bot = Bot(token=BOT_TOKEN)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load data helpers
def load_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(data, file_path):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

users_data = load_json(DATA_FILE)
items = load_json(ITEMS_FILE)

# Membership check
def is_channel_member(user_id):
    try:
        member_status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return member_status in ['member', 'administrator', 'creator']
    except TelegramError as e:
        print(f"Error checking membership: {e}")
        return False

# Start command
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or ""
    referrer_id = context.args[0] if context.args else None

    if user_id not in users_data:
        users_data[user_id] = {
            "first_name": first_name,
            "last_name": last_name,
            "referrals": 0
        }
        if referrer_id and referrer_id != user_id and referrer_id in users_data:
            users_data[referrer_id]["referrals"] += 1
            context.bot.send_message(
                chat_id=int(referrer_id),
                text=f"{first_name} has joined the bot through your referral link!"
            )
    save_json(users_data, DATA_FILE)

    if not is_channel_member(user_id):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        update.message.reply_photo(
            photo="https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Telegram_access_denied.jpg/800px-Telegram_access_denied.jpg",
            caption="Access Denied 🚫\n\nPlease join the channel to use the bot.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        referral_link = f"https://t.me/{bot.username}?start={user_id}"
        welcome_msg = (
            f"Welcome, {first_name} {last_name}! 🎉\n\n"
            "Available commands:\n"
            "/gen - Get a random megalink\n"
            "/alive - Check bot status\n"
            "/help - Get help\n"
            "/referral - View your referral count\n\n"
            f"Your referral link: {referral_link}"
        )
        update.message.reply_text(welcome_msg)

# Generate command
def gen(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_channel_member(user_id):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        update.message.reply_photo(
            photo="https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Telegram_access_denied.jpg/800px-Telegram_access_denied.jpg",
            caption="Access Denied 🚫\n\nPlease join the channel to use this command.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if users_data.get(user_id, {}).get("referrals", 0) < 3:
        update.message.reply_text("❗️ You need to refer at least 3 friends to use this command.")
        return

    if not items:
        update.message.reply_text("No items available.")
        return

    item = random.choice(items)
    update.message.reply_photo(photo=item['image'], caption=f"Enjoy mawa...❤️\nLink: {item['url']}")

# Other command handlers with channel check
def alive(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_channel_member(user_id):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        update.message.reply_photo(
            photo="https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Telegram_access_denied.jpg/800px-Telegram_access_denied.jpg",
            caption="Access Denied 🚫\n\nPlease join the channel to use this command.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    update.message.reply_text("Bot is Alive ⚡")

def help_command(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_channel_member(user_id):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        update.message.reply_photo(
            photo="https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Telegram_access_denied.jpg/800px-Telegram_access_denied.jpg",
            caption="Access Denied 🚫\n\nPlease join the channel to use this command.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    help_msg = (
        "Available commands:\n"
        "/gen - Get a random item 🎁\n"
        "/alive - Check bot status 🏃‍♂️\n"
        "/help - Get help ❓\n"
        "/referral - View your referral count 👥"
    )
    update.message.reply_text(help_msg)

def referral(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_channel_member(user_id):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        update.message.reply_photo(
            photo="https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Telegram_access_denied.jpg/800px-Telegram_access_denied.jpg",
            caption="Access Denied 🚫\n\nPlease join the channel to use this command.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    referral_count = users_data.get(user_id, {}).get("referrals", 0)
    referral_link = f"https://t.me/{bot.username}?start={user_id}"

    keyboard = [[InlineKeyboardButton("Share Referral Link", url=f"https://t.me/share/url?url={referral_link}")]]
    update.message.reply_text(
        f"You have referred {referral_count} friends. 📈\n"
        f"Use your unique referral link to invite others:\n{referral_link}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# Admin-only handlers
def data(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
        temp_file.write(json.dumps(users_data, indent=4).encode('utf-8'))
        temp_file_path = temp_file.name

    with open(temp_file_path, 'rb') as file:
        context.bot.send_document(chat_id=ADMIN_ID, document=file, filename='users_data.json')

def add_item(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) < 2:
        update.message.reply_text("Please provide a URL and an image link.")
        return

    url, image_url = context.args[:2]
    items.append({"url": url, "image": image_url})
    save_json(items, ITEMS_FILE)
    update.message.reply_text("Item added successfully!")

def stats(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    blocked_users = sum(1 for user in users_data.values() if user.get("blocked", False))
    active_users = len(users_data) - blocked_users
    new_users_today = sum(1 for user in users_data.values() if user.get("date_joined", "") == time.strftime("%Y-%m-%d"))

    stats_msg = (
        f"📊 Bot Statistics:\n\n"
        f"Total Users: {len(users_data)}\n"
        f"Active Users: {active_users}\n"
        f"Blocked Users: {blocked_users}\n"
        f"New Users Today: {new_users_today}"
    )
    update.message.reply_text(stats_msg)
# Function to send user data to the admin every hour
def hourly_data_send(context: CallbackContext):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
        temp_file.write(json.dumps(users_data, indent=4).encode('utf-8'))
        temp_file_path = temp_file.name

    with open(temp_file_path, 'rb') as file:
        context.bot.send_document(chat_id=ADMIN_ID, document=file, filename='users_data.json')

    os.remove(temp_file_path)  # Clean up temporary file


def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    job_queue = updater.job_queue

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gen", gen))
    dp.add_handler(CommandHandler("alive", alive))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("referral", referral))
    dp.add_handler(CommandHandler("data", data))
    dp.add_handler(CommandHandler("additem", add_item))
    dp.add_handler(CommandHandler("stats", stats))

    dp.add_error_handler(error_handler)

    job_queue.run_repeating(hourly_data_send, interval=3600, first=0)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
