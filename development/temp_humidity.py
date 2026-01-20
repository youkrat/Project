'''
from machine import I2C, Pin 
import time

class AHT30:
    def __init__(self, i2c, address=0x38):
        self.i2c = i2c
        self.address = address
        time.sleep(0.1)

        # Initialize sensor
        self.i2c.writeto(self.address, b'\xBE\x08\x00')
        time.sleep(0.01)

    def read(self):
        # Trigger measurement
        self.i2c.writeto(self.address, b'\xAC\x33\x00')
        time.sleep(0.08)

        data = self.i2c.readfrom(self.address, 6)

        humidity = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
        temperature = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

        humidity = humidity * 100 / 1048576
        temperature = temperature * 200 / 1048576 - 50

        return temperature, humidity

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = AHT30(i2c)

while True:
    temp, hum = sensor.read()
    print(f"Temperature: {temp:.2f} °C")
    print(f"Humidity: {hum:.2f} %")
    print("-------------")
    time.sleep(2)

'''
'''
from machine import I2C, Pin
import time

# ESP32 I2C pins (adjust if needed)
i2c = I2C(
    0,
    scl=Pin(22),
    sda=Pin(21),
    freq=400000
)

devices = i2c.scan()
print("I2C devices:", devices)

AHT30_ADDR = 0x38

def read_aht30():
    # Trigger measurement
    i2c.writeto(AHT30_ADDR, bytes([0xAC, 0x33, 0x00]))
    time.sleep_ms(80)

    data = i2c.readfrom(AHT30_ADDR, 6)

    raw_hum = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    raw_temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

    humidity = raw_hum * 100 / 1048576
    temperature = raw_temp * 200 / 1048576 - 50

    return temperature, humidity


while True:
    t, h = read_aht30()
    print("Temp:", round(t, 2), "C  Humidity:", round(h, 2), "%")
    time.sleep(2)

'''

from machine import Pin, I2C, ADC
from time import sleep, time
import json

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

            raw_h = ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4))
            raw_t = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5])

            humidity = (raw_h / 1048576) * 100
            temperature = (raw_t / 1048576) * 200 - 50

            return round(temperature, 2), round(humidity, 2), True
        except:
            return None, None, False


# I2C setup
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
aht30 = AHT30(i2c)

# LDR setup
ldr = ADC(Pin(32))
ldr.atten(ADC.ATTN_11DB)
ldr.width(ADC.WIDTH_12BIT)

def read_light_lux():
    raw = ldr.read()
    lux = (raw / 4095) * 1000
    return round(lux, 1)

def read_sensors():
    temperature, humidity, aht_ok = aht30.read()
    lux = read_light_lux()

    return {
        "timestamp": time(),
        "temperature_c": temperature,
        "humidity_percent": humidity,
        "light_lux": lux,
        "status": {
            "aht30": aht_ok,
            "light": True
        }
    }

while True:
    print(json.dumps(read_sensors()))
    sleep(2)
