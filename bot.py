import datetime
import time

from vkbottle import GroupEventType, GroupTypes, Keyboard, Text, VKAPIError
from vkbottle import BaseStateGroup, bot
from typing import Optional
from vkbottle import Keyboard, KeyboardButtonColor, Text
import vkbottle
from typing import Union
from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule

import numpy as np
import re


class VkBot:
    bot: bot.Bot()
    room_dict: dict
    user_data: dict[int: dict["day": datetime.datetime, "time": datetime.datetime, "room": str, "pc": list()]]
    days_buttons = ['', '', '']
    pcs_buttons = list()

    class AllStates(BaseStateGroup):
        main_state = "main"
        day_state = "day"
        day_spec_state = "day_spec"
        time_state = "time"
        help_state = "help"
        room_state = "room"
        pc_state = "pc"

    def __init__(self, langame):
        self.api = langame
        with open('config.txt', 'r') as f:
            tmp_str = f.readline()
            while tmp_str != '':
                if tmp_str[-1] == '\n':
                    tmp_str = tmp_str[:-1]
                if tmp_str[:10] == 'bot_token=':
                    tmp_str = tmp_str[10:]
                    break
                tmp_str = f.readline()
        self.bot = vkbottle.Bot(tmp_str)

        self.room_dict = {}
        with open('rooms.txt', 'r') as f:
            tmp_str = f.readline()
            while tmp_str != '':
                if tmp_str[-1] == '\n':
                    tmp_str = tmp_str[:-1]
                self.room_dict[tmp_str[:tmp_str.find(':')]] = tmp_str[tmp_str.find(':') + 1:].split(',')
                tmp_str = f.readline()
        self.user_data = {0: {"day": datetime.datetime.now(), "time": datetime.datetime.now(), "room": '', "pc": []}}
        for i in self.room_dict:
            self.pcs_buttons += self.room_dict[i]

    def loop(self):
        # 1
        @self.bot.on.message(text=["Помощь"], state=self.AllStates.main_state)
        async def help_handler(message: Message):
            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.help_state)
            keyboard = (
                Keyboard(one_time=True, inline=False)
                .add(Text("Назад в меню"))
            ).get_json()

            await message.answer(
                message="--текст помощи--",
                keyboard=keyboard
            )
            return

        # 2
        @self.bot.on.message(text=["Начать бронирование"], state=self.AllStates.main_state)
        async def day_handler(message: Message):
            if not (message.from_id.real in self.user_data.keys()):
                self.user_data[message.from_id.real] = {\
                    "day": datetime.datetime.now(),
                    "time": datetime.datetime.now(),\
                    "room": "",\
                    "pc": []}

            self.days_buttons[0] = "Сегодня " + datetime.datetime.strftime(datetime.datetime.now(), '%d.%m')
            self.days_buttons[1] = "Завтра " + datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%d.%m')
            self.days_buttons[2] = "Послезавтра " + datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=2), '%d.%m')
            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.day_state)
            keyboard = (
                Keyboard(one_time=True, inline=False)
                .add(Text(self.days_buttons[0]), color=KeyboardButtonColor.POSITIVE)
                .add(Text(self.days_buttons[1]), color=KeyboardButtonColor.POSITIVE)
                .row()
                .add(Text(self.days_buttons[2]), color=KeyboardButtonColor.POSITIVE)
                .add(Text("Другой день"), color=KeyboardButtonColor.POSITIVE)
                .row()
                .add(Text("Назад в меню"))
            ).get_json()

            await message.answer(
                message="Выберите день",
                keyboard=keyboard
            )
            return

        # 3
        @self.bot.on.message(text=["Другой день"], state=self.AllStates.day_state)
        async def day_spec_handler(message: Message):
            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.day_spec_state)
            keyboard = (
                Keyboard(one_time=True, inline=False)
                .add(Text("Назад в меню"))
            ).get_json()

            await message.answer(
                message="Выберите дату по формату \"дд мм\", например \"16 02\"",
                keyboard=keyboard
            )
            return

        # 4, 6
        @self.bot.on.message(state=self.AllStates.day_spec_state)
        async def time0_handler(message: Message):
            chosen_day_str = message.text
            try:
                self.user_data[message.from_id.real]['day'] = datetime.datetime.strptime(chosen_day_str, '%d %m')
            except(ValueError):
                keyboard = (
                    Keyboard(one_time=True, inline=False)
                    .add(Text("Назад в меню"))
                ).get_json()

                await message.answer(
                    message="Неверный формат даты. Выберите дату по формату \"дд мм\", например \"16 02\"",
                    keyboard=keyboard
                )
                return
            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.time_state)
            keyboard = (
                Keyboard(one_time=True, inline=False)
                .add(Text("Назад в меню"))
            ).get_json()

            await message.answer(
                message="Выберите время по формату \"чч мм\", например \"12 00\"",
                keyboard=keyboard
            )
            return

        # 5
        @self.bot.on.message(regexp=self.days_buttons, state=self.AllStates.day_state)
        async def time1_handler(message: Message):
            self.user_data[message.from_id.real]['day'] = datetime.datetime.strptime((message.text[-5:] + '.' + \
                datetime.datetime.strftime(datetime.datetime.now(), '%Y')), "%d.%m.%Y")

            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.time_state)
            keyboard = (
                Keyboard(one_time=True, inline=False)
                .add(Text("Назад в меню"))
            ).get_json()

            await message.answer(
                message="Введите время по формату \"чч мм\", например \"12 00\"",
                keyboard=keyboard
            )
            return

        # 7-8
        @self.bot.on.message(state=self.AllStates.time_state)
        async def room_handler(message: Message):
            chosen_time_str = message.text
            this_user_id = message.from_id.real
            try:
                self.user_data[this_user_id]['time'] = datetime.datetime.strptime(chosen_time_str, '%H %M')
            except(ValueError):
                keyboard = (
                    Keyboard(one_time=True, inline=False)
                    .add(Text("Назад в меню"))
                ).get_json()

                await message.answer(
                    message="Неверный формат времени. Введите время по формату \"чч мм\", например \"12 00\"",
                    keyboard=keyboard
                )
                return
            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.room_state)
            kb = Keyboard(one_time=True, inline=False)
            cnt = 0
            for i in self.room_dict.keys():
                kb.add(Text(i), color=KeyboardButtonColor.POSITIVE)
                cnt += 1
                if cnt == 3:
                    cnt = 0
                    kb.row()
            kb.add(Text("Назад в меню"))
            keyboard = kb.get_json()

            msg_text = "Выберите комнату"

            table = self.api.get_reservation_table([], datetime.datetime(
                year=self.user_data[this_user_id]['day'].year,
                month=self.user_data[this_user_id]['day'].month,
                day=self.user_data[this_user_id]['day'].day,
                hour=self.user_data[this_user_id]['time'].hour,
                minute=self.user_data[this_user_id]['time'].minute
            ), True)
            for i in self.room_dict.keys():
                cnt = 0
                for j in self.room_dict[i]:
                    tmp_bool = False
                    for k in table[j]:
                        if k:
                            tmp_bool = True
                    if not tmp_bool:
                        cnt += 1
                msg_text += ("\nЗал " + i + " свободно мест " + str(cnt))

            await message.answer(
                message=msg_text,
                keyboard=keyboard
            )
            return

        # 9
        @self.bot.on.message(regexp=self.room_dict.keys(), state=self.AllStates.room_state)
        async def pc_handler(message: Message):
            this_user_id = message.from_id.real
            self.user_data[this_user_id]['room'] = message.text

            tmp_time = datetime.datetime(
                year=self.user_data[this_user_id]['day'].year,
                month=self.user_data[this_user_id]['day'].month,
                day=self.user_data[this_user_id]['day'].day,
                hour=self.user_data[this_user_id]['time'].hour,
                minute=self.user_data[this_user_id]['time'].minute)
            pc_list = {}
            for i in self.room_dict[self.user_data[this_user_id]['room']]:
                pc_list[i] = tmp_time
            table = self.api.get_reservation_table(pc_list, tmp_time, False)
            for i in table:
                if table[i][0]:
                    del pc_list[i]
                    continue
                for j in range(len(table[i])):
                    if table[i][j]:
                        pc_list[i] = tmp_time + (j * datetime.timedelta(minutes=30))
                        break

            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.pc_state)
            kb = Keyboard(one_time=True, inline=False)
            cnt = 0
            msg_text = "Выберите ПК"
            for i in pc_list:
                msg_text += ("\n" + (i + 'пк свободен до ' + datetime.datetime.strftime(pc_list[i], '%H:%M')))
                kb.add(Text(i), color=KeyboardButtonColor.POSITIVE)
                cnt += 1
                if cnt == 4:
                    cnt = 0
                    kb.row()
            if cnt != 0:
                kb.row()
            kb.add(Text("Назад в меню"))
            keyboard = kb.get_json()

            await message.answer(
                message=msg_text,
                keyboard=keyboard
            )
            return

        # 10
        @self.bot.on.message(regexp=self.pcs_buttons, state=self.AllStates.pc_state)
        async def book_handler(message: Message):
            this_user_id = message.from_id.real

            if len(self.user_data[this_user_id]['pc']) == 100:
                await self.bot.state_dispenser.set(message.peer_id, self.AllStates.main_state)
                keyboard = (
                    Keyboard(one_time=True, inline=False)
                    .add(Text("Начать бронирование"), color=KeyboardButtonColor.POSITIVE)
                    .row()
                    .add(Text("Помощь"), color=KeyboardButtonColor.POSITIVE)
                ).get_json()

                await message.answer(
                    message="Не больше 3 болнирований компьютеров на человека\n--текст мэйн--",
                    keyboard=keyboard
                )
                return

            tmp_time = datetime.datetime(
                year=self.user_data[this_user_id]['day'].year,
                month=self.user_data[this_user_id]['day'].month,
                day=self.user_data[this_user_id]['day'].day,
                hour=self.user_data[this_user_id]['time'].hour,
                minute=self.user_data[this_user_id]['time'].minute)
            self.api.set_reservation(tmp_time, message.text, (await self.bot.api.users.get(message.from_id))[0].first_name)
            self.user_data[this_user_id]['pc'].append(message.text)
            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.main_state)
            keyboard = (
                Keyboard(one_time=True, inline=False)
                .add(Text("Начать бронирование"), color=KeyboardButtonColor.POSITIVE)
                .row()
                .add(Text("Помощь"), color=KeyboardButtonColor.POSITIVE)
            ).get_json()

            await message.answer(
                message="Сделана бронь на имя " + (await self.bot.api.users.get(message.from_id))[0].first_name + "\n--текст мэйн--",
                keyboard=keyboard
            )
            return

        # 11
        @self.bot.on.message(text='Назад в меню')
        async def menu_handler(message: Message):
            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.main_state)
            keyboard = (
                Keyboard(one_time=True, inline=False)
                .add(Text("Начать бронирование"), color=KeyboardButtonColor.POSITIVE)
                .row()
                .add(Text("Помощь"), color=KeyboardButtonColor.POSITIVE)
            ).get_json()

            await message.answer(
                message="--текст мейн--",
                keyboard=keyboard
            )
            return

        # !
        @self.bot.on.message()
        async def all_handler(message: Message):
            await self.bot.state_dispenser.set(message.peer_id, self.AllStates.main_state)
            keyboard = (
                Keyboard(one_time=True, inline=False)
                .add(Text("Начать бронирование"), color=KeyboardButtonColor.POSITIVE)
                .row()
                .add(Text("Помощь"), color=KeyboardButtonColor.POSITIVE)
            ).get_json()

            await message.answer(
                message="--текст мейн--",
                keyboard=keyboard
            )
            return

        self.bot.run_forever()
