import urequests

def get_weather(api_key, city):
    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        f"?appid={api_key}&q={city}"
    )
    r = urequests.get(url)
    data = r.json()
    r.close()
    return data
