'''
File Structure:
project/
│
├── main.py                # Orchestration only (loop, glue)
│
├── config.py              # Constants & configuration
│
├── sensors/
│   ├── __init__.py
│   ├── aht30.py            # AHT30 driver
│   └── light.py            # LDR abstraction
│
├── network/
│   ├── __init__.py
│   ├── wifi.py             # WiFi connection
│   └── weather_api.py      # OpenWeatherMap client
│
├── logic/
│   ├── __init__.py
│   ├── time_utils.py       # Time + timezone logic
│   └── day_night.py        # Light trend inference
│
├── storage/
│   ├── __init__.py
│   ├── sdcard_fs.py        # SD mounting
│   └── logger.py           # JSONL logging
│
└── utils/
    ├── __init__.py
    └── conversions.py      # Temperature conversions


'''

'''
Workflow mental model:
Sensors ─┐
         ├──► payload ───► print → Node-RED(display over the web)
API ─────┘              └──► append → SD (/sd/*.jsonl)

'''

from machine import Pin, I2C, ADC #type: ignore
from time import sleep, time

from config import *
from aht30 import AHT30
from light import LightSensor
from wifi import connect
from weather_api import get_weather
from day_night import time_of_day_from_trend, stable_time_state
from time_utils import Time
from sdcard_fs import mount_sd
from conversions import convert_temp
from nodered import send as send_to_nodered
from logger import log as log_to_sd
from statistics import (
    mean,
    moving_average,
    median,
    min_max_range,
    std_dev
)


def get_weather_offline():
    return {
        "temperature_c": None,
        "temperature_f": None,
        "description": "offline",
        "sunrise": None,
        "sunset": None
    }


# Setup
connect(SSID, PASSWORD)
mount_sd()

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
aht = AHT30(i2c)

ldr_adc = ADC(Pin(32))
ldr_adc.atten(ADC.ATTN_11DB)
ldr_adc.width(ADC.WIDTH_12BIT)
ldr = LightSensor(ldr_adc)

lux_history = []
local_temp_history = []
api_temp_history = []
cached_api = None
last_api_time = 0

while True:
    now = time()

    temp, hum = aht.read()
    if temp is None:
        sleep(1)
        continue

    lux = ldr.read_lux()
    lux_history.append(lux)
    lux_history[:] = lux_history[-LUX_HISTORY_SIZE:]
    lux_avg = mean(lux_history)
    lux_smooth = moving_average(lux_history, window=10)
    lux_median = median(lux_history)
    lux_min, lux_max, lux_range = min_max_range(lux_history)
    lux_std = std_dev(lux_history)

    state = stable_time_state(time_of_day_from_trend(lux_history))

    if cached_api is None or now - last_api_time >= API_INTERVAL:
        raw = get_weather(API_KEY, CITY)
        tc, tf = convert_temp(raw["main"]["temp"])
        cached_api = {
            "temperature_c": tc,
            "temperature_f": tf,
            "description": raw["weather"][0]["description"],
            "sunrise": str(Time(raw["sys"]["sunrise"], raw["timezone"])),
            "sunset": str(Time(raw["sys"]["sunset"], raw["timezone"]))
        }
        last_api_time = now

    payload = {
        "timestamp": now,
        "local": {
            "temperature_c": temp,
            "humidity_percent": hum,
            "light_lux": lux,
            "time_of_day": state
        },
        "api": cached_api
    }
    payload["stats"] = {
    "lux_mean": lux_avg,
    "lux_moving_avg": lux_smooth,
    "lux_median": lux_median,
    "lux_min": lux_min,
    "lux_max": lux_max,
    "lux_range": lux_range,
    "lux_std": lux_std
    }


    send_to_nodered(payload)
    log_to_sd(payload)

    sleep(1.2)
