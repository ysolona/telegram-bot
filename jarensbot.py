import telebot
from telebot import types
import sqlite3
import random
import logging
from pathlib import Path

# ================= BOT SETTINGS =================
TOKEN = "8744362866:AAEwkODXKmUfJK3WfytKwZA3xQ8bM5RYCTw"
ADMIN_ID = 8010525201

bot = telebot.TeleBot(TOKEN)

# ================= USER STATES =================
user_states = {}
selected_product = {}

# ================= SAVE DIRECTORY =================
SAVE_DIR = Path("saved_items")
SAVE_DIR.mkdir(exist_ok=True)

# ================= STOCK FOLDER =================
Path("stock").mkdir(exist_ok=True)

# ================= PRODUCT PATHS =================
PRODUCT_PATHS = {
    "Roblox Account With Info": "/storage/emulated/0/Jaren’s Bot /Stock/roblox.txt",
    "Codm Account With Info": "/storage/emulated/0/Jaren’s Bot /Stock/codm.txt",
    "Mlbb Account With Info": "/storage/emulated/0/Jaren’s Bot /Stock/mlbb.txt"
}

# ================= LOAD EXISTING ITEMS =================
def load_existing_items():
    saved_items = set()

    for file_path in SAVE_DIR.rglob("*.txt"):
        try:
            with file_path.open("r", errors="ignore") as f:
                saved_items.update(line.strip() for line in f)

        except Exception as e:
            logging.error(f"❌ Error reading {file_path}: {e}")

    return saved_items

existing_items = load_existing_items()

# ================= DATABASE =================
conn = sqlite3.connect("store.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item TEXT
)
""")

conn.commit()

# ================= FUNCTIONS =================
def get_balance(user_id):

    cursor.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data is None:

        cursor.execute(
            "INSERT INTO users(user_id, balance) VALUES(?, ?)",
            (user_id, 0)
        )

        conn.commit()
        return 0

    return data[0]


def add_balance(user_id, amount):

    bal = get_balance(user_id)

    cursor.execute(
        "UPDATE users SET balance=? WHERE user_id=?",
        (bal + amount, user_id)
    )

    conn.commit()


def remove_balance(user_id, amount):

    bal = get_balance(user_id)

    cursor.execute(
        "UPDATE users SET balance=? WHERE user_id=?",
        (bal - amount, user_id)
    )

    conn.commit()


def get_item(path):

    file_path = Path(path)

    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        items = [line.strip() for line in f if line.strip()]

    if not items:
        return None

    item = random.choice(items)

    items.remove(item)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(items))

    return item

# ================= MAIN MENU =================
def main_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("📦 Generate")
    btn2 = types.KeyboardButton("💰 Balance")
    btn3 = types.KeyboardButton("💳 Add Balance")
    btn4 = types.KeyboardButton("📜 History")

    markup.add(btn1)
    markup.add(btn2, btn3)
    markup.add(btn4)

    return markup

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id
    get_balance(user_id)

    text = """
🌻 Jarens Private Account Store

💎 Premium Stock
💸 Price: ₱1 each
⚡ Instant Delivery

📌 Available Products:
Roblox account with info 
Codm Account With Info 
Mlbb Account With Info 
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )

# ================= BUTTONS =================
@bot.message_handler(func=lambda m: True)
def buttons(message):

    user_id = message.from_user.id

    # ================= GENERATE MENU =================
    if message.text == "📦 Generate":

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        btn1 = types.KeyboardButton("Roblox Account With Info")
        btn2 = types.KeyboardButton("Codm Account With Info")
        btn3 = types.KeyboardButton("Mlbb Account With Info")
        back = types.KeyboardButton("🔙 Back")

        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)
        markup.add(back)

        bot.send_message(
            message.chat.id,
            "📦 Choose a product:",
            reply_markup=markup
        )

    # ================= PRODUCT SELECT =================
    elif message.text in PRODUCT_PATHS:

        selected_product[user_id] = message.text
        user_states[user_id] = "waiting_quantity"

        bot.reply_to(
            message,
            "📦 How many accounts do you want to generate?\n\n⚠️ Minimum is 20."
        )

    # ================= QUANTITY INPUT =================
    elif user_states.get(user_id) == "waiting_quantity":

        if not message.text.isdigit():
            bot.reply_to(message, "❌ Please enter a valid number.")
            return

        quantity = int(message.text)

        if quantity < 20:

            bot.reply_to(
                message,
                f"⚠️ Minimum purchase amount is 20.\n\nYour input: {quantity}\n\nPlease enter a higher quantity."
            )

            return

        price_per_item = 2
        total_price = quantity * price_per_item

        bal = get_balance(user_id)

        if bal < total_price:

            bot.reply_to(
                message,
                f"❌ Not enough balance.\n\nNeeded: ₱{total_price}\nYour Balance: ₱{bal}"
            )

            return

        product_name = selected_product[user_id]

        generated_items = []

        for _ in range(quantity):

            item = get_item(PRODUCT_PATHS[product_name])

            if item is None:
                break

            generated_items.append(item)

        if not generated_items:
            bot.reply_to(message, "❌ Out of stock")
            return

        remove_balance(
            user_id,
            len(generated_items) * price_per_item
        )

        for item in generated_items:

            cursor.execute(
                "INSERT INTO history(user_id, item) VALUES(?, ?)",
                (user_id, item)
            )

        conn.commit()

        result = "\n".join(generated_items)

        bot.reply_to(
            message,
            f"✅ Generated {len(generated_items)} item(s)\n\n{result}\n\n💸 Remaining Balance: ₱{get_balance(user_id)}"
        )

        user_states[user_id] = None

    # ================= BALANCE =================
    elif message.text == "💰 Balance":

        bal = get_balance(user_id)

        bot.reply_to(
            message,
            f"💰 Your Balance: ₱{bal}"
        )

    # ================= ADD BALANCE =================
    elif message.text == "💳 Add Balance":

        text = """
💳 Payment Method

GCash: 09551792231 or 09569188961
Name: J****a D****o  or R****** P******o

Send proof of payment to admin. @zvrtpd
"""

        bot.reply_to(message, text)

    # ================= HISTORY =================
    elif message.text == "📜 History":

        cursor.execute(
            "SELECT item FROM history WHERE user_id=? ORDER BY id DESC LIMIT 10",
            (user_id,)
        )

        data = cursor.fetchall()

        if not data:

            bot.reply_to(message, "📭 No history yet")
            return

        msg = "📜 Your History:\n\n"

        for x in data:
            msg += f"• {x[0]}\n"

        bot.reply_to(message, msg)

    # ================= BACK =================
    elif message.text == "🔙 Back":

        bot.send_message(
            message.chat.id,
            "🏠 Main Menu",
            reply_markup=main_menu()
        )

# ================= ADMIN ADD BALANCE =================
@bot.message_handler(commands=['addbal'])
def admin_add_balance(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        args = message.text.split()

        user_id = int(args[1])
        amount = int(args[2])

        add_balance(user_id, amount)

        bot.reply_to(message, "✅ Balance added")

    except:

        bot.reply_to(
            message,
            "Usage:\n/addbal USER_ID AMOUNT"
        )

print("✅ Bot running...")
bot.infinity_polling()