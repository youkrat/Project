import datetime as dt
import requests #type:ignore
import sys
import network #type:ignore

class Time(object): 
    ''' Represents a time of day in 24-hr format'''
    def __init__(self, timestamp, timezone_offset):
        '''defining object creation'''
        local_seconds = timestamp + timezone_offset
        seconds_in_day = local_seconds % 86400

        self.hour = seconds_in_day //3600
        self.minute = (seconds_in_day % 3600) // 60
        self.second = seconds_in_day % 60

    def __str__(self):
        return self.convert_to_string()
    
    def convert_to_string(self):
        ''' Returns time as HH:MM::SS'''
        return(
            self._pad(self.hour) + ':' +
            self._pad(self.minute) + ':' +
            self._pad(self.second)
        )
    def _pad(self, value): #meant for use within the class
        ''' Helper method for converting time'''
        if value < 10:
            return '0' + str(value)
        return str(value)
    

def getWeather(city):
    '''sig: str -> dict
    '''
    apiKey = '4274c7e18b26e6691b907dddd4d408cc'
    BASE_URL= 'http://api.openweathermap.org/data/2.5/weather?'
    url = BASE_URL + 'appid=' + apiKey + '&q=' + city 
    response = requests.get(url).json()
    return response

def converToCelsiusFahrenheit(temp):
    '''sig: int-> tuple
    Converts temp from Kelvin to Celsius and Fahrenheit'''
    celsius = temp - 273.15
    fahrenheit = celsius * (9/5)+ 32
    return celsius, fahrenheit


def connectTointernet():
    '''connects the ESP32 board to the internet to do API calls
    takes command line arguments to connect to the internet'''
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect('Ben', 'benmwangi1')
    return station.isconnected()

if len(sys.argv) == 3 and sys.argv[1] == "-c":
    City = sys.argv[2]
    response = getWeather(City)
else:
    print('Usage: weather.py -c <City>')

connected = False
while not connected:
    connected = connectTointernet()

tempKevin = response['main']['temp']
tempCelsius, tempFahrenheit = converToCelsiusFahrenheit(tempKevin)
feelsLikeKevin = response['main']['feels_like']
feelsLikeCelsius, feelsLikeFahrenheit = converToCelsiusFahrenheit(feelsLikeKevin)
humidity = response['main']['humidity']
description = response['weather'][0]['description']

timeLastUpdated = Time(response['dt'], response['timezone'])
sunriseTime = Time(response['sys']['sunrise'] , response['timezone']) 
sunsetTime = Time(response['sys']['sunset'] , response['timezone'])
windSpeed = response['wind']['speed']

print(f"Temperature in {City}: {tempCelsius:.2f} °C or {tempFahrenheit:.2f} °F")
print(f"Temperature in {City} feels like: {feelsLikeCelsius:.2f} °C or {feelsLikeFahrenheit:.2f} °F")
print(f"Humidity in {City}: {humidity}%")
print(f"Wind Speed in {City}: {windSpeed}m/s")
print(f"Last Updated {timeLastUpdated}")
print(f"Sun rises in {City}: {sunriseTime} local time")
print(f"Sun sets in {City} at : {sunsetTime} local time")
print(f"General weather in {City}: {description}")
