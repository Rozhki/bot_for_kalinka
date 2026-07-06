import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise RuntimeError(
        "Не задан bot_token в файле .env"
    )

if ADMIN_ID == 0:
    raise RuntimeError(
        "Не задан admin_id в файле .env"
    )
