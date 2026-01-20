from machine import I2C #type:ignore
from time import sleep, sleep_us

MASK_RS = 0x01
MASK_E  = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4

class LCD_I2C:
    def __init__(self, i2c, addr, rows, cols):
        self.i2c = i2c
        self.addr = addr
        self.rows = rows
        self.cols = cols
        self.backlight = 1
        sleep(0.05)
        self.init_lcd()

    def write_byte(self, data):
        self.i2c.writeto(self.addr, bytes([data]))

    def pulse_enable(self, data):
        self.write_byte(data | MASK_E)
        sleep_us(10)
        self.write_byte(data & ~MASK_E)
        sleep_us(200)

    def write4bits(self, nibble, mode=0):
        data = ((nibble << SHIFT_DATA) |
               (self.backlight << SHIFT_BACKLIGHT) | mode)
        self.pulse_enable(data)

    def send(self, value, mode=0):
        self.write4bits(value >> 4, mode)
        self.write4bits(value & 0x0F, mode)

    def command(self, cmd):
        self.send(cmd, 0)
        if cmd == 0x01 or cmd == 0x02:
            sleep(0.002)

    def write_char(self, char):
        self.send(ord(char), MASK_RS)

    def init_lcd(self):
        # Reset sequence
        self.write4bits(0x03)
        sleep(0.005)
        self.write4bits(0x03)
        sleep(0.005)
        self.write4bits(0x03)
        sleep(0.005)
        self.write4bits(0x02)

        # Function set: 4-bit, 2 line, 5x8 font
        self.command(0x28)
        # Display ON, cursor OFF
        self.command(0x0C)
        # Entry mode
        self.command(0x06)
        # Clear
        self.command(0x01)
        sleep(0.005)

    def clear(self):
        self.command(0x01)

    def move_to(self, col, row):
        offsets = [0x00, 0x40]
        self.command(0x80 | (col + offsets[row]))

    def putstr(self, string):
        for char in string:
            self.write_char(char)

    def backlight_on(self):
        self.backlight = 1
        self.write_byte(1 << SHIFT_BACKLIGHT)

    def backlight_off(self):
        self.backlight = 0
        self.write_byte(0)
