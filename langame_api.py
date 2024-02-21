from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import numpy as np


class LangameApi:
    pc_list = []
    table: np.array
    time_now: datetime
    time_units: int
    driver: webdriver

    def __time_get_str(self, x: datetime) -> str:
        return x.strftime('%d.%m.%Y %H:%M:00')  # 14.02.2024 17:30:00

    def __login(self):
        with open('config.txt', 'r') as f:
            tmp_str = f.readline()
            while tmp_str != '':
                if tmp_str[-1] == '\n':
                    tmp_str = tmp_str[:-1]
                if tmp_str[:6] == 'login=':
                    login = tmp_str[6:]
                elif tmp_str[:9] == 'password=':
                    password = tmp_str[9:]
                tmp_str = f.readline()

        elem = self.driver.find_element(By.XPATH, "//input[@id='login']")
        elem.clear()
        elem.send_keys(login)
        elem = self.driver.find_element(By.XPATH, "//input[@id='password']")
        elem.clear()
        elem.send_keys(password)
        elem.send_keys(Keys.ENTER)

    def __init__(self, time_units: int = 48):
        self.driver = webdriver.Chrome()
        self.driver.get("https://20.langame.ru")
        assert "LanGame" in self.driver.title
        self.__login()
        self.driver.get("https://20.langame.ru/reservation")
        assert "Бронирование" in self.driver.title


        with open('PCs.txt', 'r') as f:
            tmp = f.readline()
            while tmp != '':
                if tmp[-1] == '\n':
                    tmp = tmp[:-1]
                self.pc_list.append(tmp)
                tmp = f.readline()
        self.table = np.zeros((len(self.pc_list), time_units), dtype=bool)
        self.time_units = time_units
        #self.set_reservation_table()

    def get_reservation_table(self, pc_list: list[str], date_time: datetime, short_period: bool):#?date=19.02.2024+04%3A22
        self.driver.get("https://20.langame.ru/reservation/?date=" + datetime.strftime(date_time, '%d.%m.%Y')\
                        + "+" + datetime.strftime(date_time, '%H') + "%3A" + datetime.strftime(date_time, '%M'))
        if len(pc_list) == 0:
            pc_list = list(['01', '02', '03', '05', '06', '07', '10', '22', '23', '24', '25', '26', '31', '32', '33',\
                            '34', '35', '36', '37', '38', '39', '41', '42', '43', '44', '45', '46', '47', '48', '49',\
                            '50', '51', 'PS4', 'PS5(1)', 'PS5(2)', 'autosim'])
        table = {}
        start_time = datetime(date_time.year, date_time.month, date_time.day, date_time.hour,\
                                 int(date_time.minute) - int(date_time.minute) % 30, 0)
        if short_period:
            time_units = 4
        else:
            time_units = 12
        for i in pc_list:
            table[i] = list()
        for j in range(time_units):
            tmp_time = timedelta(minutes=30) * j + start_time
            time_iter = self.__time_get_str(tmp_time)
            for i in pc_list:
                xpath = "//*[@data-pc='" + i + "' and @data-time='" + time_iter + "']"
                elem = self.driver.find_element(By.XPATH, xpath)
                if elem.tag_name == 'div':
                    table[i].append(True)
                else:
                    table[i].append(False)
        self.driver.get("https://20.langame.ru/reservation")
        return table

    def set_reservation(self, time: datetime, pc: str, name: str):
        elem0 = self.driver.find_element(By.XPATH, "//*[@data-pc='" + pc + "' and @data-time='" + self.__time_get_str(time) + "']")
        elem0.click()
        elem1 = self.driver.find_element(By.XPATH, "//*[@name='fio[]']")
        elem2 = self.driver.find_element(By.XPATH, "//*[@name='phone[]']")
        elem3 = self.driver.find_element(By.XPATH, "//*[@id='reserv_comment' and @name='reserv_comment']")
        elem4 = self.driver.find_element(By.XPATH, "//*[@class='btn btn-success col-12']")
        elem1.send_keys(name)
        elem2.send_keys('9856666666')
        elem3.send_keys('Заброировано вк ботом')
        elem4.click()

    def close_session(self):
        self.driver.close()