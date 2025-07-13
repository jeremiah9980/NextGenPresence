from flask import Flask, render_template, request, redirect # type: ignore
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    conn = sqlite3.connect("devices.db")
    cur = conn.cursor()
    cur.execute("SELECT mac, last_seen, friendly_name FROM device_log ORDER BY last_seen DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("index.html", devices=rows)

@app.route("/tag", methods=["POST"])
def tag():
    mac = request.form["mac"]
    name = request.form["name"]
    conn = sqlite3.connect("devices.db")
    conn.execute("UPDATE device_log SET friendly_name = ? WHERE mac = ?", (name, mac))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

