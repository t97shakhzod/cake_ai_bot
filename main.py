"""Kirish nuqtasi — `python main.py`"""

import logging

from dotenv import load_dotenv
from telegram import Update

from bot import create_application
from config import load_settings


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    load_dotenv()
    settings = load_settings()
    application = create_application(settings)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
