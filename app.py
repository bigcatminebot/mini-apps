from flask import Flask, render_template, request, jsonify
import sqlite3
import random

app = Flask(__name__)
DB = "db.sqlite3"

def add_reward(uid: str, amount: int):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET saldo = saldo + ? WHERE telegram_id = ?", (amount, uid))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    uid = request.args.get("uid")
    return render_template("index.html", uid=uid)

@app.route("/claim-reward", methods=["POST"])
def claim_reward():
    data = request.get_json()
    uid = data.get("uid")

    if not uid:
        return jsonify({"status": "error", "message": "User ID tidak ditemukan"}), 400

    reward = random.randint(10, 25)  # Bisa disesuaikan
    add_reward(uid, reward)

    return jsonify({"status": "ok", "message": f"✅ Kamu mendapat Rp{reward}!"})

if __name__ == "__main__":
    app.run(debug=True)
