import os
import time
import json
import re
from urllib.parse import urlparse

# from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from tion_btle import S3 as Breezer
from bluepy.btle import BTLEDisconnectError


tion_s3_writable_attributes = frozenset({
    "state",
    "heater",
    "sound",
    "mode",
    "heater_temp",
    "fan_speed",
})


def normalize_mac(mac):
    return re.sub("^0x", "", re.sub("[:\\-]", "", tion_mac)).lower()


def on_connect(mqtt_client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    mqtt_client.subscribe('tion/' + '0x' + normalize_mac(tion_mac) + '/set/#')


def on_message(mqtt_client, userdata, msg):
    print("topic:" + msg.topic + " " + str(msg.payload))

    try:
        topic, mac, command, attr_name = msg.topic.split("/", 4)
    except ValueError:
        return

    if topic != 'tion':
        print("Unknown topic", topic)
        return

    if normalize_mac(mac) != normalize_mac(tion_mac):
        print("Unknown mac", topic)
        return

    if command != 'set':
        print("Set command expected")
        return

    if attr_name not in tion_s3_writable_attributes:
        print("Attribute " + attr_name + " isn't writable")
        return

    attr_value = msg.payload.decode('utf-8')

    new_state = dict([(attr_name, attr_value)])
    print("pretending to set: " + str(new_state))
    device.set(new_state)

    tion_state = device.get()

    tion_publish(mqtt_client, tion_mac, tion_state)


def tion_publish(mqtt_client, tion_mac, tion_state):
    tion_state = {
        **tion_state,
        **{"online": "online"},
    }
    mqtt_client.publish(
        "tion/" + "0x" + normalize_mac(tion_mac),
        json.dumps(tion_state),
        retain=True,
    )

    for attr_name, attr_value in tion_state.items():
        mqtt_client.publish(
            "tion/" + "0x" + normalize_mac(tion_mac) + '/' + attr_name,
            attr_value,
            retain=True,
        )


# load_dotenv()

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_settings = urlparse(os.getenv("MOSQUITTO_URL"))
tion_mac = os.getenv("TION_MAC")

mqtt_client.username_pw_set(mqtt_settings.username, mqtt_settings.password)

mqtt_client.connect(mqtt_settings.hostname, mqtt_settings.port or 1883)

run = True

device = Breezer(tion_mac)

try:
    print("Start: Reading tion state")
    tion_state = device.get()

    print(str(tion_state))

    tion_publish(mqtt_client, tion_mac, tion_state)

    print("Done: Reading tion state")

    # device.set({'state': 'on'})

except BTLEDisconnectError:
    print("Cannot connect to breezer")

while run:
    # print("mqtt loop")
    mqtt_client.loop()

    # time.sleep(1)
