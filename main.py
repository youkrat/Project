from weather import connect_to_internet, get_weather, convert_temp, Time
from lcd_display import show_message
from machine import Pin #type:ignore
import time

CITY = "Nairobi"

# ------------------------
# Setup Buttons
# ------------------------
left_btn  = Pin(14, Pin.IN, Pin.PULL_UP)   # Left button
right_btn = Pin(27, Pin.IN, Pin.PULL_UP)   # Right button

# ------------------------
# Get Weather Data Once
# ------------------------
connect_to_internet()

data = get_weather(CITY)

temp_c, temp_f = convert_temp(data["main"]["temp"])
humidity = data["main"]["humidity"]
description = data["weather"][0]["description"]

sunrise = Time(data["sys"]["sunrise"], data["timezone"])
sunset  = Time(data["sys"]["sunset"], data["timezone"])

# ------------------------
# Screen Definitions
# ------------------------
screens = [
    (CITY, f"{temp_c}C Hum:{humidity}%"),
    ("Weather:", description),
    ("Sunrise", str(sunrise)),
    ("Sunset", str(sunset))
]

screen_index = 0
num_screens = len(screens)

# Show initial screen
show_message(screens[screen_index][0], screens[screen_index][1])

# ------------------------
# Simple Debounce Helper
# ------------------------
def wait_release(btn):
    while btn.value() == 0:
        time.sleep_ms(10)

# ------------------------
# Main Loop
# ------------------------
while True:
    if left_btn.value() == 0:     # button pressed (active-low)
        screen_index -= 1
        if screen_index < 0:
            screen_index = num_screens - 1
        show_message(screens[screen_index][0], screens[screen_index][1])
        wait_release(left_btn)

    if right_btn.value() == 0:    # button pressed
        screen_index += 1
        if screen_index >= num_screens:
            screen_index = 0
        show_message(screens[screen_index][0], screens[screen_index][1])
        wait_release(right_btn)

    time.sleep_ms(50)
