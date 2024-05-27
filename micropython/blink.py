#pip install esptool

from machine import Pin
import time

led_pin = Pin(2,Pin.OUT)

while True:
    led_pin.on()
    time.sleep(1)
    led_pin.off()
    time.sleep(1)

#esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
#esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 esp32-20190125-v1.10.bin