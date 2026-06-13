"""
Main Entry Point
Flask health server + Telegram bot dono saath start karta hai.
"""

import asyncio
import logging
from health_server import start_health_server
from bot import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

async def main():
    start_health_server()
    log.info("✅ Health server started")

    log.info("🤖 Bot starting...")
    await app.start()
    log.info("✅ Bot started! Listening for messages...")

    # Bot ko alive rakhne ke liye
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
