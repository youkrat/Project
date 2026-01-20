import os
from machine import SPI, Pin
import sdcard
from config import SD_MOUNT_POINT

def mount_sd():
    spi = SPI(2, baudrate=10_000_000,
              sck=Pin(18), mosi=Pin(23), miso=Pin(19))
    cs = Pin(5, Pin.OUT)
    sd = sdcard.SDCard(spi, cs)
    os.mount(sd, SD_MOUNT_POINT)
