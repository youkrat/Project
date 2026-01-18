'''
Ben Kimani
Comp112Z
Project Title: Weather Authenticator
'''

'''
The project's simple goal is to compare local weather readings with official 
online weather data to evaluate the reliability of provided weather information.
'''


'''
Goals for 1st phase
1. Retrieve weather data from the internet using a public weather API(Most
the calls and operations are done on an ESP32 microcontroller connected to
a DHT11 temperature sensor, a photoresistor and an LCD screen)
2. Parse JSON-formatted API responses and extract temperature and related
values(This is achieved by using loop conditionals, dictionarties and string 
operatuions to create a formatting rubric)
3. Store weather data in a CSV file for logging and future analysis
4. Use local temperature readings and lighting conditions to determine
the time of day using simple conditionals and trends
5. Compute simple statistical values from the data e.g 
absolute difference between values
average temperature difference over multiple readings
minimum and maximum recorded temperature
Percentage deviation from API temperature 
SImple trend detection(Increasing or decreasing over time)

#An additional might be adding unifromly generated random values to try 
and simulate how temperature proceeds from day to night in preparation for extraction
of actual data 
'''

import paho.mqtt.client as mqtt
print("MQTT OK")
