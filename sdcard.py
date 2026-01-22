# sdcard.py
# MicroPython SD card driver (SPI mode)

from machine import SPI, Pin
import os

class SDCard:
    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs
        self.cs.init(self.cs.OUT, value=1)
        self.init_card()

    def init_card(self):
        self.cs.value(1)
        for _ in range(10):
            self.spi.write(b'\xff')
        self.cs.value(0)
        self.spi.write(b'\x40\x00\x00\x00\x00\x95')
        self.cs.value(1)
        self.spi.write(b'\xff')

    def readblocks(self, block_num, buf):
        self.cs.value(0)
        self.spi.write(b'\x51')
        self.spi.write(block_num.to_bytes(4, 'big'))
        self.spi.write(b'\x00')
        while self.spi.read(1)[0] != 0xfe:
            pass
        self.spi.readinto(buf)
        self.cs.value(1)

    def writeblocks(self, block_num, buf):
        self.cs.value(0)
        self.spi.write(b'\x58')
        self.spi.write(block_num.to_bytes(4, 'big'))
        self.spi.write(b'\x00')
        self.spi.write(b'\xfe')
        self.spi.write(buf)
        self.cs.value(1)

    def ioctl(self, op, arg):
        if op == 4:  # get number of blocks
            return 0
        if op == 5:  # get block size
            return 512
