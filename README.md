ESP32 Weather Station (Offline-First)

OVERVIEW
This project implements an ESP32-based weather station that collects local environmental data, performs on-device analysis, and streams structured JSON data to a host machine for visualization and storage.

The system is designed with an offline-first, modular architecture, prioritizing reliability on constrained hardware while preserving a clear separation between sensing, logic, networking, and storage.


SYSTEM ARCHITECTURE

Sensors ─┐
         ├──► payload ───► Serial output → Node-RED (visualization & storage)
API ─────┘

The ESP32 acts as a data acquisition and preprocessing node.
All data is streamed over USB serial.
Node-RED serves as the gateway for dashboards and persistence.


CORE FEATURES

Local sensing:
- Temperature and humidity via AHT30 (I2C)
- Ambient light via LDR (ADC)

On-device analysis:
- Mean, median, standard deviation
- Minimum, maximum, and range
- Moving average
- Time-of-day inference based on light intensity trends
- Hysteresis to prevent oscillation between day and night states

Structured output:
- One JSON object per sample
- Designed for machine ingestion (Node-RED, logging, replay)


REPOSITORY STRUCTURE

project/
├── main.py                  Final single-file runtime (offline, serial)
├── development/             Modular and experimental development code
│   ├── aht30.py
│   ├── statistics.py
│   ├── time_utils.py
│   ├── timeOfDay.py
│   ├── wifi.py
│   ├── weather_api.py
│   ├── sdcard.py
│   ├── sdcard_fs.py
│   ├── logger.py
│   └── nodered.py
└── README.md


DEVELOPMENT VS RUNTIME CODE

The development directory contains modular and exploratory implementations used to test:
- Wi-Fi connectivity
- API access
- SD card logging
- Separation of concerns

Some features could not reliably run on the ESP32 due to:
- MicroPython driver limitations
- Blocking SPI behavior (SD card)
- Unstable Wi-Fi behavior in constrained environments

timeOfDay.py provides a consolidated reference implementation showing how the system was ideally intended to operate in a fully modular setup.


FINAL RUNTIME DESIGN

Due to reliability considerations, the deployed version:
- Uses a single-file runtime (main.py)
- Disables Wi-Fi
- Disables SD card logging
- Streams all data over USB serial
- Delegates visualization and storage to Node-RED on the host machine

This approach eliminates blocking I/O on the ESP32, ensures deterministic behavior, and preserves the full data pipeline conceptually.


DATA OUTPUT FORMAT

Each sample is emitted as a single JSON object, for example:

{
  "timestamp": 1705800000,
  "mode": "offline_serial",
  "local": {
    "temperature_c": 24.3,
    "humidity_percent": 61.2,
    "light_lux": 420.1,
    "time_of_day": "Day"
  },
  "api": {
    "description": "offline_stub"
  },
  "stats": {
    "lux_mean": 415.2,
    "lux_median": 410.0,
    "lux_std": 22.4
  }
}

This format is compatible with:
- Node-RED dashboards
- JSON Lines (JSONL) logging
- Offline replay and analysis


KNOWN LIMITATIONS

- SD card access via SPI may block indefinitely under MicroPython
- Wi-Fi reliability depends on network and environment
- Environment variables (.env) are not supported on MicroPython


AUTHOR
Ben Mwangi
