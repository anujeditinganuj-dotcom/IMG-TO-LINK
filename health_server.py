import os
import threading
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"status": "running", "bot": "Image To Link Bot", "version": "2.0.0"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

def start_health_server():
    t = threading.Thread(target=run_flask, daemon=False)
    t.start()
