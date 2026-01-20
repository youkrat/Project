from time import sleep

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
            if len(data) != 6:
                return None, None

            raw_h = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
            raw_t = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

            humidity = (raw_h / 1048576) * 100
            temperature = (raw_t / 1048576) * 200 - 50
            return round(temperature, 2), round(humidity, 2)

        except Exception:
            return None, None
