import requests #type:ignore
import os
from dotenv import load_dotenv #type: ignore
import time
import json
from time import sleep

load_dotenv()

API_KEY = os.getenv('API_KEY')

BASE_PATH = "."  # "." for PC, "/sd" for ESP32


if API_KEY is None:
    raise RuntimeError("API_KEY not found. Is .env loaded?")

def get_weather(city):
    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        "?appid=" + API_KEY + "&q=" + city
    )
    response = requests.get(url)
    data = response.json()
    response.close()
    return data

def build_weather_record(api_data): #for now
    ts = int(time.time())

    record = {
        "ts" : ts,
        "iso": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(ts)
        ), #Human-readable UTC time
        "temperature" : api_data["main"]["temp"],
        "weather description" : api_data["weather"][0]["description"]

    }
    return record


def get_log_filename():
    date = time.strftime("%Y-%m-%d", time.localtime())
    return f"{BASE_PATH}/weather_{date}.jsonl"

def log_to_sd(record):
    filename = get_log_filename()

    with open(filename, "a") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()


def main_loop():
    while True:
        data = get_weather("Nairobi")
        record = build_weather_record(data)

        log_to_sd(record)

        sleep(100)

main_loop()