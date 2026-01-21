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
# --- NO WIFI ---
# connect(SSID, PASSWORD)
ENABLE_SD = False   # ← flip to True only if SD is stable

if ENABLE_SD:
    mount_sd()


mount_sd()

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
aht = AHT30(i2c)

ldr_adc = ADC(Pin(32))
ldr_adc.atten(ADC.ATTN_11DB)
ldr_adc.width(ADC.WIDTH_12BIT)
ldr = LightSensor(ldr_adc)

lux_history = []
local_temp_history = []

cached_api = get_weather_offline()   # <-- offline stub

while True:
    now = time()

    # -------- LOCAL SENSORS --------
    temp, hum = aht.read()
    if temp is None:
        sleep(1)
        continue

    lux = ldr.read_lux()

    # --- histories ---
    lux_history.append(lux)
    lux_history[:] = lux_history[-LUX_HISTORY_SIZE:]

    local_temp_history.append(temp)
    local_temp_history[:] = local_temp_history[-LUX_HISTORY_SIZE:]

    # -------- STATISTICS --------
    lux_avg = mean(lux_history)
    lux_smooth = moving_average(lux_history, window=10)
    lux_median = median(lux_history)
    lux_min, lux_max, lux_range = min_max_range(lux_history)
    lux_std = std_dev(lux_history)

    # -------- TIME OF DAY --------
    state = stable_time_state(
        time_of_day_from_trend(lux_history)
    )

    # -------- PAYLOAD --------
    payload = {
        "timestamp": now,
        "mode": "offline",   # Hit a wall with WiFi capabilities
        "local": {
            "temperature_c": temp,
            "humidity_percent": hum,
            "light_lux": lux,
            "time_of_day": state
        },
        "api": cached_api,
        "stats": {
            "lux_mean": lux_avg,
            "lux_moving_avg": lux_smooth,
            "lux_median": lux_median,
            "lux_min": lux_min,
            "lux_max": lux_max,
            "lux_range": lux_range,
            "lux_std": lux_std
        }
    }

    print(payload)
    if ENABLE_SD:
      log_to_sd(payload)


    sleep(1.2)
