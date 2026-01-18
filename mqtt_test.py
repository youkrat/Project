from umqtt.simple import MQTTClient
import network
import time

SSID = "Ben"
PASSWORD = "benmwangi1"
BROKER = "172.26.4.185"  # NOT localhost

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
    print("WiFi connected:", wlan.ifconfig())

connect_wifi()

client = MQTTClient("esp32_test", BROKER)
client.connect()

while True:
    client.publish("weather/test", "hello from esp32")
    print("Published")
    time.sleep(5)
