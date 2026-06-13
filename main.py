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
    # Flask health server background mein start karo
    start_health_server()
    log.info("✅ Health server started")

    # Telegram bot polling start karo
    log.info("🤖 Bot starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    app.run()
