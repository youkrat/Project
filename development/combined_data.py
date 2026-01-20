from machine import Pin, I2C, ADC #type: ignore
from time import sleep, time
import json
import network #type: ignore
import urequests
import os
from dotenv import load_dotenv #type: ignore

'''
Weather Station Program
-----------------------
This program runs on an ESP32 using MicroPython.

It:
1. Reads local environmental data using physical sensors:
   - AHT30 (temperature + humidity)
   - LDR (light intensity)
2. Fetches remote weather data from OpenWeatherMap (once per minute)
3. Performs trend-based reasoning on light data to infer time of day
4. Outputs a combined JSON payload suitable for Node-RED visualization
'''

# =======================
# CONFIG
# =======================
CITY = "Nairobi"
API_KEY = os.getenv('API_KEY')
SSID = os.getenv('SSID')
PASSWORD = os.getenv('PASSWORD')

API_INTERVAL = 60  # seconds

# =======================
# LIGHT ANALYSIS CONFIG
# =======================
LUX_HISTORY_SIZE = 60     # last 60 seconds
DAY_THRESHOLD = 300
NIGHT_THRESHOLD = 100
TREND_EPSILON = 10

# =======================
# GLOBAL STATE (FIX #1)
# =======================
last_time_state = "Unknown"

# =======================
# TIME CLASS
# =======================
class Time:
    def __init__(self, timestamp, timezone_offset):
        local_seconds = timestamp + timezone_offset
        seconds_in_day = local_seconds % 86400
        self.hour = seconds_in_day // 3600
        self.minute = (seconds_in_day % 3600) // 60

    def __str__(self):
        return self._pad(self.hour) + ":" + self._pad(self.minute)

    def _pad(self, v):
        return "0" + str(v) if v < 10 else str(v)

# =======================
# AHT30 SENSOR
# =======================
class AHT30:
    def __init__(self, i2c, address=0x38):
        self.i2c = i2c
        self.address = address
        self.i2c.writeto(self.address, b'\xBE\x08\x00')
        sleep(0.02)

    def read(self):
        try:
            self.i2c.writeto(self.address, b'\xAC\x33\x00')
            sleep(0.08)
            data = self.i2c.readfrom(self.address, 6)

            if len(data) != 6:
                return None, None

            raw_h = ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4))
            raw_t = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5])

            humidity = (raw_h / 1048576) * 100
            temperature = (raw_t / 1048576) * 200 - 50

            return round(temperature, 2), round(humidity, 2)

        except:
            return None, None

# =======================
# WIFI + API
# =======================
def connect_to_internet():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        sleep(1)

    print("WiFi connected:", wlan.ifconfig())
    sleep(3)  # allow WiFi to stabilize
    return True

def get_weather(city):
    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        "?appid=" + API_KEY + "&q=" + city
    )
    r = urequests.get(url)
    data = r.json()
    r.close()
    return data

def convert_temp(k):
    c = k - 273.15
    f = c * 9 / 5 + 32
    return round(c, 1), round(f, 1)

# =======================
# TIME OF DAY LOGIC
# =======================
def time_of_day_from_trend(lux_history):
    """
    sig: list[float] -> str
    Determines time of day using trend analysis.
    """

    if len(lux_history) < 10:
        return "Unknown"

    mid = len(lux_history) // 2
    if mid == 0:                      # FIX #2
        return "Unknown"

    first_avg = sum(lux_history[:mid]) / mid
    second_avg = sum(lux_history[mid:]) / (len(lux_history) - mid)

    delta = second_avg - first_avg

    if second_avg > DAY_THRESHOLD and delta > TREND_EPSILON:
        return "Day"

    if second_avg < NIGHT_THRESHOLD and delta < -TREND_EPSILON:
        return "Night"

    if delta < -TREND_EPSILON:
        return "Approaching Night"

    if delta > TREND_EPSILON:
        return "Approaching Day"

    return "Stable"

def stable_time_state(new_state):
    global last_time_state

    if new_state in ["Day", "Night"]:
        last_time_state = new_state

    return last_time_state

# =======================
# HARDWARE SETUP
# =======================
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
aht30 = AHT30(i2c)

ldr = ADC(Pin(32))
ldr.atten(ADC.ATTN_11DB)
ldr.width(ADC.WIDTH_12BIT)

# =======================
# API CACHE
# =======================
last_api_time = 0
cached_api = None

lux_history = []

# =======================
# STARTUP
# =======================
connect_to_internet()

# =======================
# MAIN LOOP
# =======================
while True:
    now = time()

    # -----------------------
    # SENSOR DATA (every second)
    # -----------------------
    local_temp, local_humidity = aht30.read()

    if local_temp is None or local_humidity is None:
        sleep(1)
        continue

    light_lux = round((ldr.read() / 4095) * 1000, 1)

    # -----------------------
    # UPDATE LUX HISTORY
    # -----------------------
    lux_history.append(light_lux)
    if len(lux_history) > LUX_HISTORY_SIZE:
        lux_history.pop(0)

    # -----------------------
    # TIME OF DAY ANALYSIS
    # -----------------------
    raw_state = time_of_day_from_trend(lux_history)
    time_state = stable_time_state(raw_state)

    local_data = {
        "temperature_c": local_temp,
        "humidity_percent": local_humidity,
        "light_lux": light_lux,
        "time_of_day": time_state
    }

    # -----------------------
    # API DATA (once per minute)
    # -----------------------
    if cached_api is None or (now - last_api_time) >= API_INTERVAL:
        try:
            api_raw = get_weather(CITY)

            api_temp_c, api_temp_f = convert_temp(api_raw["main"]["temp"])
            sunrise = Time(api_raw["sys"]["sunrise"], api_raw["timezone"])
            sunset = Time(api_raw["sys"]["sunset"], api_raw["timezone"])

            cached_api = {
                "city": CITY,
                "temperature_c": api_temp_c,
                "temperature_f": api_temp_f,
                "humidity_percent": api_raw["main"]["humidity"],
                "sunrise": str(sunrise),
                "sunset": str(sunset),
                "description": api_raw["weather"][0]["description"]
            }

            last_api_time = now

        except Exception as e:
            print("API error:", e)

    # -----------------------
    # COMBINED PAYLOAD
    # -----------------------
    payload = {
        "timestamp": now,
        "local": local_data,
        "api": cached_api
    }

    try:
        print(json.dumps(payload))
    except:
        print("{}")

    sleep(1.2)  # FIX #3 — prevents serial/REPL instability
