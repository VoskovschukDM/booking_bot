import selenium
import vkbottle
from bot import VkBot
from langame_api import LangameApi

from datetime import datetime, timedelta
import time

langame = LangameApi()

vk_bot = VkBot(langame)
vk_bot.loop()

#langame.close_session()

#pyinstaller --noconfirm --onedir --console --name "booking_bot" --add-data "C:/Progs/booking_bot/config.txt;." --add-data "C:/Progs/booking_bot/PCs.txt;." --add-data "C:/Progs/booking_bot/rooms.txt;." --hidden-import "vkbottle" --hidden-import "selenium"  "C:/Progs/booking_bot/main.py"