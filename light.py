class LightSensor:
    def __init__(self, adc):
        self.adc = adc

    def read_lux(self):
        return round((self.adc.read() / 4095) * 1000, 1)
