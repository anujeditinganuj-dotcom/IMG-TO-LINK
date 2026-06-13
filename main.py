import asyncio
import logging
from health_server import start_health_server
from bot import app
from pyrogram import idle

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def main():
    start_health_server()
    log.info("✅ Health server started")
    await app.start()
    log.info("✅ Bot started!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
