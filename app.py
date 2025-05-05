import sqlite3
from flask import Flask, request, render_template, jsonify
import threading
import telebot

API_TOKEN = "7148397099:AAFIqHsRJ4OAJ5_RGHNUBQ5BT5aE3a5HPAM"  # Ganti dengan token kamu
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
DB = "database.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id TEXT UNIQUE, saldo INTEGER DEFAULT 0, referrer_id TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id TEXT, amount INTEGER, status TEXT)")
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/claim-reward", methods=["POST"])
def claim_reward():
    data = request.get_json()
    uid = data.get("uid")
    if not uid:
        return jsonify({"status": "fail", "message": "User ID tidak valid."})
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT saldo FROM users WHERE telegram_id = ?", (uid,))
    result = c.fetchone()
    if result:
        c.execute("UPDATE users SET saldo = saldo + 20 WHERE telegram_id = ?", (uid,))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "message": "✅ +20 saldo ditambahkan!"})
    conn.close()
    return jsonify({"status": "fail", "message": "User tidak ditemukan."})

@bot.message_handler(commands=['start'])
def start(message):
    ref_id = message.text.split(" ")[1] if len(message.text.split()) > 1 else None
    telegram_id = str(message.from_user.id)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (telegram_id, saldo, referrer_id) VALUES (?, ?, ?)", (telegram_id, 20, ref_id))
        if ref_id:
            c.execute("UPDATE users SET saldo = saldo + 100 WHERE telegram_id = ?", (ref_id,))
        conn.commit()
        bot.reply_to(message, "✅ Kamu berhasil terdaftar! Gunakan #wallet untuk cek saldo.")
    else:
        bot.reply_to(message, "⚠️ Kamu sudah terdaftar.")
    conn.close()

@bot.message_handler(func=lambda msg: msg.text == "#wallet")
def wallet(message):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT saldo FROM users WHERE telegram_id = ?", (str(message.from_user.id),))
    result = c.fetchone()
    conn.close()
    if result:
        bot.reply_to(message, f"💰 Saldo kamu: Rp{result[0]}")
    else:
        bot.reply_to(message, "❌ Kamu belum terdaftar. Gunakan /start.")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=5000)


@bot.message_handler(func=lambda msg: msg.text.startswith("#withdraw"))
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
            bot.reply_to(message, f"✅ Permintaan withdraw Rp{amount} dikirim ke admin. Tunggu konfirmasi.")
        else:
            bot.reply_to(message, "❌ Saldo tidak cukup atau jumlah tidak valid (min Rp1).")
        conn.close()
    except:
        bot.reply_to(message, "⚠️ Format salah. Gunakan: #withdraw 1000")

@bot.message_handler(commands=['admin_withdraws'])
def admin_list_withdraws(message):
    if str(message.from_user.id) != "YOUR_ADMIN_ID":  # Ganti dengan ID admin kamu
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
    if str(message.from_user.id) != "YOUR_ADMIN_ID":
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

