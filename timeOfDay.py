"""
ESP32 Weather Station (MicroPython)

Reads local sensor data (AHT30 + LDR), fetches remote weather data from
OpenWeatherMap, infers time-of-day from light trends, and outputs a
JSON payload suitable for Node-RED visualization.
"""
from dotenv import load_dotenv #type: ignore
from machine import Pin, I2C, ADC #type:ignore
from time import sleep, time
import json
import network #type: ignore
import urequests
import os

load_dotenv()

# Configuration
API_KEY = os.getenv('API_KEY')
CITY = "Nairobi"
SSID = os.getenv('SSID')
PASSWORD = os.getenv('PASSWORD')

if API_KEY is None:
    raise RuntimeError('WEATHER_API_KEY not set')


API_INTERVAL = 60
LUX_HISTORY_SIZE = 60
DAY_THRESHOLD = 180
NIGHT_THRESHOLD = 60
TREND_EPSILON = 5

last_time_state = "Unknown"


class Time:
    """Local time derived from a Unix timestamp and timezone offset."""

    def __init__(self, timestamp: int, timezone_offset: int):
        local_seconds = timestamp + timezone_offset
        seconds_in_day = local_seconds % 86400
        self.hour = seconds_in_day // 3600
        self.minute = (seconds_in_day % 3600) // 60

    def __str__(self) -> str:
        return f"{self._pad(self.hour)}:{self._pad(self.minute)}"

    @staticmethod
    def _pad(value: int) -> str:
        return f"0{value}" if value < 10 else str(value)


class AHT30:
    """I2C driver for the AHT30 temperature and humidity sensor."""

    def __init__(self, i2c: I2C, address: int = 0x38):
        self.i2c = i2c
        self.address = address
        self.i2c.writeto(self.address, b"\xBE\x08\x00")
        sleep(0.02)

    def read(self) -> tuple:
        """Return (temperature_c, humidity_percent) or (None, None)."""
        try:
            self.i2c.writeto(self.address, b"\xAC\x33\x00")
            sleep(0.08)
            data = self.i2c.readfrom(self.address, 6)

            if len(data) != 6:
                return None, None

            raw_h = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
            raw_t = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

            humidity = (raw_h / 1048576) * 100
            temperature = (raw_t / 1048576) * 200 - 50

            return round(temperature, 2), round(humidity, 2)

        except Exception:
            return None, None


def connect_to_internet() -> bool:
    """Connect to WiFi and block until connected."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        sleep(1)

    print("WiFi connected:", wlan.ifconfig())
    sleep(3)
    return True


def get_weather(city: str) -> dict:
    """Fetch current weather data for a city from OpenWeatherMap."""
    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        f"?appid={API_KEY}&q={city}"
    )
    r = urequests.get(url)
    data = r.json()
    r.close()
    return data


def convert_temp(kelvin: float) -> tuple:
    """Convert Kelvin to (Celsius, Fahrenheit)."""
    c = kelvin - 273.15
    f = c * 9 / 5 + 32
    return round(c, 1), round(f, 1)


def time_of_day_from_trend(lux_history: list) -> str:
    """Infer time-of-day from light intensity trends."""
    if len(lux_history) < 10:
        return "Unknown"

    mid = len(lux_history) // 2
    if mid == 0:
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


def stable_time_state(new_state: str) -> str:
    """Stabilize time-of-day output to avoid rapid oscillation."""
    global last_time_state
    if new_state in ("Day", "Night"):
        last_time_state = new_state
    return last_time_state


# Hardware setup
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
aht30 = AHT30(i2c)

ldr = ADC(Pin(32))
ldr.atten(ADC.ATTN_11DB)
ldr.width(ADC.WIDTH_12BIT)

cached_api = None
last_api_time = 0
lux_history = []

connect_to_internet()


while True:
    now = time()

    temperature, humidity = aht30.read()
    if temperature is None or humidity is None:
        sleep(1)
        continue

    light_lux = round((ldr.read() / 4095) * 1000, 1)

    lux_history.append(light_lux)
    if len(lux_history) > LUX_HISTORY_SIZE:
        lux_history.pop(0)

    time_state = stable_time_state(
        time_of_day_from_trend(lux_history)
    )

    local_data = {
        "temperature_c": temperature,
        "humidity_percent": humidity,
        "light_lux": light_lux,
        "time_of_day": time_state
    }

    if cached_api is None or (now - last_api_time) >= API_INTERVAL:
        try:
            api_raw = get_weather(CITY)

            temp_c, temp_f = convert_temp(api_raw["main"]["temp"])
            sunrise = Time(api_raw["sys"]["sunrise"], api_raw["timezone"])
            sunset = Time(api_raw["sys"]["sunset"], api_raw["timezone"])

            cached_api = {
                "city": CITY,
                "temperature_c": temp_c,
                "temperature_f": temp_f,
                "humidity_percent": api_raw["main"]["humidity"],
                "sunrise": str(sunrise),
                "sunset": str(sunset),
                "description": api_raw["weather"][0]["description"]
            }

            last_api_time = now

        except Exception:
            pass

    payload = {
        "timestamp": now,
        "local": local_data,
        "api": cached_api
    }

    print(json.dumps(payload))
    sleep(1.2)
