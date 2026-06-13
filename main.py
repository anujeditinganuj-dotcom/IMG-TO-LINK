"""
Main Entry Point
Flask health server + Telegram bot dono saath start karta hai.
"""

import asyncio
import logging
import threading
import os
from health_server import app as flask_app
from bot import app
from pyrogram import idle

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

def run_flask():
    port = int(os.getenv("PORT", 8080))
    log.info(f"✅ Flask starting on port {port}")
    flask_app.run(host="0.0.0.0", port=port, debug=False)

async def main():
    # Flask ko background thread mein start karo
    t = threading.Thread(target=run_flask, daemon=False)  # daemon=False zaroori hai
    t.start()
    log.info("✅ Health server started")

    log.info("🤖 Bot starting...")
    await app.start()
    log.info("✅ Bot started! Listening for messages...")

    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
