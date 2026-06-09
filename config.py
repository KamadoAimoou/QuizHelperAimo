from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables.")

DOWNLOADS_DIR = "data/downloads"

os.makedirs(DOWNLOADS_DIR, exist_ok = True)

