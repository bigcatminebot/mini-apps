import sqlite3
from flask import Flask, request, render_template, jsonify
import threading
import telebot

API_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Ganti dengan token kamu
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