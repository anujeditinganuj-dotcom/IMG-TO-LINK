"""
Flask Health Check Server
Platforms (Railway, Render, Koyeb) ke liye PORT bind karna zaroori hota hai.
Ye server background mein chalta hai aur /health endpoint provide karta hai.
"""

import os
import threading
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "status": "running",
        "bot": "Image To Link Bot",
        "version": "2.0.0"
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

def start_health_server():
    """Background thread mein Flask start karo."""
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
