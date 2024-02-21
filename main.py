#import selenium
#import vkbottle
from bot import VkBot
from langame_api import LangameApi

langame = LangameApi()

vk_bot = VkBot(langame)
vk_bot.loop()
