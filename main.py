"""Kirish nuqtasi — `python main.py`"""

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv
from telegram import Update

from bot import create_application
from config import load_settings

# Render uchun "yolg'onchi" port ochish funksiyasi
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def run_health_check_server():
    # Render avtomatik beradigan PORT ni oladi, bo'lmasa 8080
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logging.info(f"Health check serveri {port}-portda ishga tushdi.")
    httpd.serve_forever()

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    load_dotenv()
    
    # Bot ishga tushishidan oldin portni alohida oqimda yoqamiz
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    settings = load_settings()
    application = create_application(settings)
    
    logging.info("Bot polling rejimi ishga tushmoqda...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
