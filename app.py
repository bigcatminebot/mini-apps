# app.py
import telebot
from flask import Flask, render_template, request
from flask_cors import CORS
import sqlite3
import threading

TOKEN = "7148397099:AAFIqHsRJ4OAJ5_RGHNUBQ5BT5aE3a5HPAM"
ADMIN_ID = "6046360096"
DB = "database.db"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__, template_folder="templates")
CORS(app)

# --- INIT DATABASE ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            saldo INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            amount INTEGER,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- START ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    telegram_id = str(message.from_user.id)
    args = message.text.split()
    ref_id = args[1] if len(args) > 1 else None

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (telegram_id, saldo) VALUES (?, 0)", (telegram_id,))
        if ref_id and ref_id != telegram_id:
            c.execute("UPDATE users SET saldo = saldo + 100 WHERE telegram_id = ?", (ref_id,))
            c.execute("UPDATE users SET saldo = saldo + 20 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()
    bot.reply_to(message, "✅ Kamu terdaftar! Gunakan #wallet untuk cek saldo.")

# --- CEK SALDO ---
@bot.message_handler(func=lambda m: m.text == "#wallet")
def check_wallet(message):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT saldo FROM users WHERE telegram_id = ?", (str(message.from_user.id),))
    result = c.fetchone()
    saldo = result[0] if result else 0
    bot.reply_to(message, f"💰 Saldo kamu: Rp{saldo}")
    conn.close()

# --- WITHDRAW ---
@bot.message_handler(func=lambda m: m.text.startswith("#withdraw"))
def withdraw(message):
    try:
        amount = int(message.text.split()[1])
        telegram_id = str(message.from_user.id)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT saldo FROM users WHERE telegram_id = ?", (telegram_id,))
        result = c.fetchone()
        if result and result[0] >= amount and amount >= 1:
            new_saldo = result[0] - amount
            c.execute("UPDATE users SET saldo = ? WHERE telegram_id = ?", (new_saldo, telegram_id))
            c.execute("INSERT INTO withdrawals (telegram_id, amount, status) VALUES (?, ?, ?)", (telegram_id, amount, "pending"))
            conn.commit()
            bot.reply_to(message, f"✅ Permintaan withdraw Rp{amount} dikirim ke admin.")
        else:
            bot.reply_to(message, "❌ Saldo tidak cukup atau jumlah tidak valid (min Rp1).")
        conn.close()
    except:
        bot.reply_to(message, "⚠️ Format salah. Gunakan: #withdraw 1000")

# --- ADMIN: LIST WITHDRAWS ---
@bot.message_handler(commands=['admin_withdraws'])
def admin_list_withdraws(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, telegram_id, amount FROM withdrawals WHERE status = 'pending'")
    rows = c.fetchall()
    conn.close()
    if rows:
        msg = "\n".join([f"ID: {r[0]} | User: {r[1]} | Rp{r[2]}" for r in rows])
        bot.reply_to(message, f"📋 Withdraw pending:\n{msg}\nGunakan /confirm_withdraw <id>")
    else:
        bot.reply_to(message, "✅ Tidak ada withdraw pending.")

@bot.message_handler(commands=['confirm_withdraw'])
def confirm_withdraw(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    try:
        wid = int(message.text.split()[1])
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("UPDATE withdrawals SET status = 'confirmed' WHERE id = ?", (wid,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Withdraw ID {wid} dikonfirmasi.")
    except:
        bot.reply_to(message, "⚠️ Format salah. Gunakan: /confirm_withdraw <id>")

# --- WEBAPP (update saldo via POST) ---
@app.route("/reward", methods=["POST"])
def reward():
    data = request.json
    telegram_id = data.get("telegram_id")
    amount = data.get("amount", 0)
    if telegram_id and amount:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("UPDATE users SET saldo = saldo + ? WHERE telegram_id = ?", (amount, telegram_id))
        conn.commit()
        conn.close()
        return {"status": "success"}
    return {"status": "failed"}, 400

@app.route("/")
def index():
    return render_template("index.html")

# --- START BOT THREAD ---
def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_bot).start()
    app.run(debug=True)
