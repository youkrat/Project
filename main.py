

'''
Workflow mental model:
Sensors ─┐
         ├──► payload ───► print → Node-RED(display over the web)
API ─────┘              └──► append → SD (/sd/*.jsonl)

'''

"""
ESP32 Weather Station (OFFLINE / SERIAL STREAM)

- Reads AHT30 (temp + humidity)
- Reads LDR (light)
- Infers time-of-day from light trend
- Computes basic statistics
- Emits ONE JSON object per line over USB serial
- Uses FILLER API data (no Wi-Fi, no SD)
"""

from machine import Pin, I2C, ADC  # type: ignore
from time import sleep, time
import json

# =======================
# CONFIG (HARDCODED)
# =======================
CITY = "Nairobi"

LUX_HISTORY_SIZE = 60
DAY_THRESHOLD = 180
NIGHT_THRESHOLD = 60
TREND_EPSILON = 5

last_time_state = "Unknown"

# =======================
# SENSOR DRIVERS
# =======================

class AHT30:
    def __init__(self, i2c, address=0x38):
        """sig: int -> None
        Initializes the AHT30 sensor on the given I2C bus"""
        self.i2c = i2c
        self.address = address
        self.i2c.writeto(self.address, b"\xBE\x08\x00")
        sleep(0.02)

    def read(self):
        """ sig: self -> tuple[float | None, float|None]
        Read temperature and humidity from the sensor
        Returns either (temperature_c, humidity_percent) or (None, None) on failure"""
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
        """ sig: -> NoneType
        Initializes a light sensor backed by an ADC channel"""
        self.adc = adc

    def read_lux(self):
        """ sig: LightSensor -> NoneType
        Reads current ambient light level (scaled ADC value)"""
        return round((self.adc.read() / 4095) * 1000, 1)


#Typical light level over the recent time window
def mean(data):
    """sig: list[float] -> float
    Finds the arithmetic mean of a dataset"""
    return sum(data) / len(data) if data else 0

#The middle value in stored data, data size can be changed by resizing the array
def median(data):
    """sig: list[float] -> float
    Finds the median using a sort-based selection algorithm"""
    if not data:
        return 0
    s = sorted(data)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


#How much values deviate from the mean
def std_dev(data):
    """sig: list[float] -> float
    Finds the population stanard deviation"""
    if len(data) < 2:
        return 0
    m = mean(data)
    return (sum((x - m) ** 2 for x in data) / len(data)) ** 0.5


#Brightest and darkest light(in our case, observed recently)
def min_max_range(data):
    """sig: list[float] -> tuple[float,float,float]
    Finds minimum, maximum, and range of a dataset"""
    if not data:
        return 0, 0, 0
    return min(data), max(data), max(data) - min(data)


#Looks for the mean of the most recent N values
def moving_average(data, window=10):
    """sig: list[float] -> float
    COmputes a trailing moving average over the most recent sample"""
    if len(data) < window:
        return mean(data)
    return sum(data[-window:]) / window

# =======================
# DAY / NIGHT LOGIC
# =======================

def time_of_day_from_trend(lux_history):
    """sig: list[float] -> str
    Uses directional change and a sliding moving window of light samples
    to infer time-of-day based on light intensity and trend analysis"""

    if len(lux_history) < 10:
        return "Unknown"

    mid = len(lux_history) // 2
    first_avg = sum(lux_history[:mid]) / mid
    second_avg = sum(lux_history[mid:]) / (len(lux_history) - mid)
    delta = second_avg - first_avg

    if second_avg > DAY_THRESHOLD and delta > TREND_EPSILON:
        return "Day"
    if second_avg < NIGHT_THRESHOLD and delta < -TREND_EPSILON:
        return "Night"
    if delta > TREND_EPSILON:
        return "Approaching Day"
    if delta < -TREND_EPSILON:
        return "Approaching Night"

    return "Stable"


def stable_time_state(new_state):
    """sig: str -> str
    Stabilize time-of-day classification using hysteresis
    Prevents rapid oscillation vetween states due to noisy data values"""
    global last_time_state
    if new_state in ("Day", "Night"):
        last_time_state = new_state
    return last_time_state

# =======================
# FILLER API DATA
# =======================

def get_api_stub():
    """
    sig: None -> dict[str, object]:
    Return placeholder API data when network access is unavailable.
    """
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
temp_history = []

api_data = get_api_stub()

print("ESP32 OFFLINE MODE — SERIAL STREAM STARTED")

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

    temp_history.append(temp)
    temp_history[:] = temp_history[-LUX_HISTORY_SIZE:]

    lux_avg = mean(lux_history)
    lux_med = median(lux_history)
    lux_min, lux_max, lux_rng = min_max_range(lux_history)
    lux_std = std_dev(lux_history)
    lux_smooth = moving_average(lux_history)

    state = stable_time_state(
        time_of_day_from_trend(lux_history)
    )

    payload = {
        "timestamp": now,
        "mode": "offline_serial",
        "local": {
            "temperature_c": temp,
            "humidity_percent": hum,
            "light_lux": lux,
            "time_of_day": state
        },
        "api": api_data,
        "stats": {
            "lux_mean": lux_avg,
            "lux_median": lux_med,
            "lux_min": lux_min,
            "lux_max": lux_max,
            "lux_range": lux_rng,
            "lux_std": lux_std,
            "lux_moving_avg": lux_smooth
        }
    }

    print(json.dumps(payload))
    sleep(1.2)
