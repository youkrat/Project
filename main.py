from weather import (
    connect_to_internet,
    get_weather,
    convert_temp,
    Time
)
from lcd_display import show_message
import time

CITY = "Nairobi"

connect_to_internet()

data = get_weather(CITY)

temp_c, temp_f = convert_temp(data["main"]["temp"])
humidity = data["main"]["humidity"]
description = data["weather"][0]["description"]

sunrise = Time(data["sys"]["sunrise"], data["timezone"])
sunset = Time(data["sys"]["sunset"], data["timezone"])



#Prints data sequentially due to limitations on lcd size
while True:
    # Screen 1
    show_message(
        CITY,
        str(temp_c) + "C " + 'Hum: '+ str(humidity) + "%"
    )
    time.sleep(3)

    # Screen 2
    show_message(
        "Weather:",
        description
    )
    time.sleep(3)

    # Screen 3
    show_message(
        "Sunrise",
        str(sunrise)
    )
    time.sleep(3)

    # Screen 4
    show_message(
        "Sunset",
        str(sunset)
    )
