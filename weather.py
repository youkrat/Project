

import time
import requests

API_KEY = "4274c7e18b26e6691b907dddd4d408cc"
SSID = "Ben"
PASSWORD = "benmwangi1"

class Time:
    def __init__(self, timestamp, timezone_offset):
        local_seconds = timestamp + timezone_offset
        seconds_in_day = local_seconds % 86400

        self.hour = seconds_in_day // 3600
        self.minute = (seconds_in_day % 3600) // 60
        self.second = seconds_in_day % 60

    def __str__(self):
        return self._pad(self.hour) + ":" + self._pad(self.minute) + ":" + self._pad(self.second)

    def _pad(self, value):
        return "0" + str(value) if value < 10 else str(value)


def connect_to_internet():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        time.sleep(1)

    return True


#Calls on the weather API to get weather of city
def get_weather(city):
    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        "?appid=" + API_KEY + "&q=" + city
    )
    response = requests.get(url)
    data = response.json()
    response.close()
    return data

#Converts temperature readings from Kelvin to Celsius and Fahrenheit
def convert_temp(temp_k):
    c = temp_k - 273.15
    f = c * 9 / 5 + 32
    return round(c, 1), round(f, 1)

print(get_weather("Nairobi"))