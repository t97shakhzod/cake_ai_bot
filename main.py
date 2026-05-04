""" `python main.py`"""

import logging
import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application

from bot import create_application
from config import load_settings

# 1. Render учун "сохта" сервер (Health Check)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")
    
    def do_HEAD(self): # Render bazan Head sorov yuboradi
        self.send_response(200)
        self.end_headers()

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logging.info(f"Health check serveri {port}-portda ишга тушди.")
    httpd.serve_forever()

# 2. Asosiy sinxron funksdiya
async def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    load_dotenv()
    
    # alohida ishga tushirish
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    settings = load_settings()
    application = create_application(settings)
    
    logging.info("Bot ишга тушмокда...")
    
    # run polling
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logging.info("Polling бошланди.")
        # bot kutish
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot тухтатилди.")
