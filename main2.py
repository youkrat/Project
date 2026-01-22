"""
ESP32 Weather Station (WiFi-enabled, NO SD)

- Reads AHT30 (temperature + humidity)
- Reads LDR (light)
- Infers time-of-day from light trends
- Fetches OpenWeatherMap data when WiFi is available
- Falls back to stub API data if WiFi/API fails
- Streams JSON over USB serial for Node-RED
"""

from machine import Pin, I2C, ADC  # type: ignore
from time import sleep, time
import json
import network  # type: ignore
import urequests

# =======================
# CONFIG (HARDCODED)
# =======================
API_KEY = ""
CITY = "Nairobi"

SSID = "Ben"
PASSWORD = "benmwangi1"

API_INTERVAL = 60
LUX_HISTORY_SIZE = 60
DAY_THRESHOLD = 180
NIGHT_THRESHOLD = 60
TREND_EPSILON = 5

last_time_state = "Unknown"

# =======================
# WIFI
# =======================

def connect_to_wifi(timeout=15):
    wlan = network.WLAN(network.STA_IF)

    if wlan.active():
        wlan.disconnect()
        wlan.active(False)
        sleep(1)

    wlan.active(True)
    sleep(1)
    wlan.connect(SSID, PASSWORD)

    start = time()
    while not wlan.isconnected():
        print("WiFi status:", wlan.status())
        if time() - start > timeout:
            print("WiFi failed — continuing offline")
            return False
        sleep(0.5)

    print("WiFi connected:", wlan.ifconfig())
    return True

wifi_ok = connect_to_wifi()

# =======================
# SENSOR DRIVERS
# =======================

class AHT30:
    def __init__(self, i2c, address=0x38):
        self.i2c = i2c
        self.address = address
        self.i2c.writeto(self.address, b"\xBE\x08\x00")
        sleep(0.02)

    def read(self):
        try:
            self.i2c.writeto(self.address, b"\xAC\x33\x00")
            sleep(0.08)
            data = self.i2c.readfrom(self.address, 6)

            raw_h = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
            raw_t = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

            humidity = (raw_h / 1048576) * 100
            temperature = (raw_t / 1048576) * 200 - 50

            return round(temperature, 2), round(humidity, 2)
        except Exception:
            return None, None


class LightSensor:
    def __init__(self, adc):
        self.adc = adc

    def read_lux(self):
        return round((self.adc.read() / 4095) * 1000, 1)

# =======================
# TIME + DAY/NIGHT LOGIC
# =======================

class Time:
    def __init__(self, timestamp, tz_offset):
        local = timestamp + tz_offset
        sec = local % 86400
        self.hour = sec // 3600
        self.minute = (sec % 3600) // 60

    def __str__(self):
        return f"{self.hour:02d}:{self.minute:02d}"


def time_of_day_from_trend(lux_history):
    if len(lux_history) < 10:
        return "Unknown"

    mid = len(lux_history) // 2
    first = sum(lux_history[:mid]) / mid
    second = sum(lux_history[mid:]) / (len(lux_history) - mid)
    delta = second - first

    if second > DAY_THRESHOLD and delta > TREND_EPSILON:
        return "Day"
    if second < NIGHT_THRESHOLD and delta < -TREND_EPSILON:
        return "Night"
    if delta > TREND_EPSILON:
        return "Approaching Day"
    if delta < -TREND_EPSILON:
        return "Approaching Night"

    return "Stable"


def stable_time_state(new_state):
    global last_time_state
    if new_state in ("Day", "Night"):
        last_time_state = new_state
    return last_time_state

# =======================
# WEATHER API
# =======================

def get_weather():
    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        f"?appid={API_KEY}&q={CITY}"
    )
    r = urequests.get(url)
    data = r.json()
    r.close()
    return data


def convert_temp(k):
    c = k - 273.15
    f = c * 9 / 5 + 32
    return round(c, 1), round(f, 1)


def api_stub():
    return {
        "city": CITY,
        "temperature_c": None,
        "temperature_f": None,
        "humidity_percent": None,
        "sunrise": None,
        "sunset": None,
        "description": "offline_stub"
    }

# =======================
# HARDWARE SETUP
# =======================

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
aht = AHT30(i2c)

ldr_adc = ADC(Pin(32))
ldr_adc.atten(ADC.ATTN_11DB)
ldr_adc.width(ADC.WIDTH_12BIT)
ldr = LightSensor(ldr_adc)

lux_history = []
cached_api = api_stub()
last_api_time = 0

print("ESP32 ONLINE MODE — SERIAL STREAM ACTIVE")

# =======================
# MAIN LOOP
# =======================

while True:
    now = time()

    temp, hum = aht.read()
    if temp is None:
        sleep(1)
        continue

    lux = ldr.read_lux()
    lux_history.append(lux)
    lux_history[:] = lux_history[-LUX_HISTORY_SIZE:]

    state = stable_time_state(
        time_of_day_from_trend(lux_history)
    )

    # ---- API (non-blocking) ----
    if wifi_ok and (now - last_api_time) >= API_INTERVAL:
        try:
            raw = get_weather()
            tc, tf = convert_temp(raw["main"]["temp"])
            sunrise = Time(raw["sys"]["sunrise"], raw["timezone"])
            sunset = Time(raw["sys"]["sunset"], raw["timezone"])

            cached_api = {
                "city": CITY,
                "temperature_c": tc,
                "temperature_f": tf,
                "humidity_percent": raw["main"]["humidity"],
                "sunrise": str(sunrise),
                "sunset": str(sunset),
                "description": raw["weather"][0]["description"]
            }

            last_api_time = now
        except Exception:
            pass

    payload = {
        "timestamp": now,
        "mode": "wifi_serial",
        "local": {
            "temperature_c": temp,
            "humidity_percent": hum,
            "light_lux": lux,
            "time_of_day": state
        },
        "api": cached_api
    }

    print(json.dumps(payload))
    sleep(1.2)
