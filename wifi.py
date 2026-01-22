import network #type:ignore
from time import sleep, time

SSID = "Ben"
PASSWORD = "benmwangi1"

def connect_to_internet(timeout=15) -> bool:
    """Connect to WiFi and block until connected."""

    wlan = network.WLAN(network.STA_IF)

    # Reset interface cleanly
    if wlan.active():
        wlan.disconnect()
        wlan.active(False)
        sleep(1)

    wlan.active(True)
    sleep(1)

    wlan.connect(SSID, PASSWORD)

    start = time()
    while not wlan.isconnected():
        print("WiFi status:", wlan.status())
        if time() - start > timeout:
            print("WiFi connection timed out")
            return False
        sleep(0.5)


connect_to_internet()