import os
import threading
import logging
from health_server import run_flask
from bot import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

if __name__ == "__main__":
    # Flask ko alag thread mein start karo
    t = threading.Thread(target=run_flask, daemon=False)
    t.start()
    log.info("✅ Health server started")

    # Pyrogram app.run() bot ko start aur alive rakhta hai
    log.info("🤖 Bot starting...")
    app.run()
    log.info("✅ Bot started!")
