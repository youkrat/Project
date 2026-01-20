from machine import I2C, Pin #type:ignore
from lcd_i2c import LCD_I2C
from time import sleep

# Adjust based on your LCD
I2C_ADDR = 0x27
ROWS = 2
COLS = 16

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD_I2C(i2c, I2C_ADDR, ROWS, COLS)


def show_message(line1, line2=""):
    """sig: str, str -> NoneType
    Displays two lines on LCD"""
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:16])

    lcd.move_to(0, 1)
    lcd.putstr(line2[:16])
