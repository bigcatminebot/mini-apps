from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
import sqlite3
from config import BOT_TOKEN, ADMIN_IDS

conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
cur = conn.cursor()

# ========= USER COMMANDS =========

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    telegram_id = str(user.id)
    username = user.username or ""

    ref_code = None
    if context.args:
        ref_code = context.args[0]

    # Cek apakah user sudah terdaftar
    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    data = cur.fetchone()

    if not data:
        cur.execute("INSERT INTO users (telegram_id, username, saldo, referer_id) VALUES (?, ?, ?, ?)",
                    (telegram_id, username, 20 if ref_code else 0, ref_code))
        conn.commit()

        # Tambahkan +100 ke pengundang jika ada
        if ref_code:
            cur.execute("UPDATE users SET saldo = saldo + 100 WHERE telegram_id = ?", (ref_code,))
            conn.commit()

        update.message.reply_text("✅ Kamu berhasil terdaftar di BigCat Mine!")
    else:
        update.message.reply_text("👋 Kamu sudah terdaftar.")

    # Kirimkan tombol WebApp
    webapp_button = InlineKeyboardButton(
        text="Tonton Video dan Dapatkan Reward",
        url=f"http://bigcatminebot.github.io/mini-apps?uid={telegram_id}"
    )
    reply_markup = InlineKeyboardMarkup([[webapp_button]])
    update.message.reply_text("Klik tombol di bawah ini untuk menonton video dan mendapatkan reward:", reply_markup=reply_markup)

def wallet(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    cur.execute("SELECT saldo FROM users WHERE telegram_id = ?", (user_id,))
    row = cur.fetchone()
    saldo = row[0] if row else 0
    update.message.reply_text(f"💼 Saldo kamu: Rp{saldo}")

def withdraw(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    cur.execute("SELECT saldo FROM users WHERE telegram_id = ?", (user_id,))
    row = cur.fetchone()
    saldo = row[0] if row else 0

    if saldo < 100:
        update.message.reply_text("❌ Minimal withdraw adalah Rp1 (100 poin).")
        return

    cur.execute("INSERT INTO withdraws (telegram_id, amount) VALUES (?, ?)", (user_id, saldo))
    cur.execute("UPDATE users SET saldo = 0 WHERE telegram_id = ?", (user_id,))
    conn.commit()
    update.message.reply_text("✅ Permintaan withdraw dikirim. Admin akan memproses.")

# ========= ADMIN COMMANDS =========

def panel(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS:
        update.message.reply_text("⛔ Akses ditolak.")
        return

    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT * FROM withdraws WHERE status = 'pending'")
    pending = cur.fetchall()

    message = f"👥 Total Users: {total}\n💸 Pending Withdraws: {len(pending)}\n\n"
    for wd in pending:
        message += f"• ID: {wd[0]}, User: {wd[1]}, Rp{wd[2]/100:.2f}\n"

    update.message.reply_text(message)

def confirm_withdraw(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS:
        update.message.reply_text("⛔ Akses ditolak.")
        return

    if not context.args:
        update.message.reply_text("Gunakan: /confirm <id>")
        return

    wd_id = context.args[0]
    cur.execute("UPDATE withdraws SET status = 'confirmed' WHERE id = ?", (wd_id,))
    conn.commit()
    update.message.reply_text(f"✅ Withdraw ID {wd_id} dikonfirmasi.")

# ========= SETUP BOT =========

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("withdraw", withdraw))
    dp.add_handler(CommandHandler("panel", panel))
    dp.add_handler(CommandHandler("confirm", confirm_withdraw, pass_args=True))
    dp.add_handler(MessageHandler(Filters.regex(r"^#wallet$"), wallet))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
