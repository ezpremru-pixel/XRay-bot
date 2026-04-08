import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    # Жестко вшиваем новый токен
    BOT_TOKEN = "8755858332:AAG8tzDkEkYAk3BOMiZWyLe8Cu7fctAU8Qs"
    ADMINS = [8179216822]

config = Config()
