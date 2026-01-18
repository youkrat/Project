import time
import json

while True:
    data = {
        "temperature": 24.8,
        "humidity": 57,
        "light": 720
    }

    # Send JSON over serial
    print(json.dumps(data))

    time.sleep(2)
