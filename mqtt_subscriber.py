import paho.mqtt.client as mqtt
import datetime

MQTT_SERVER = "192.168.178.58"
MQTT_BASE_TOPIC = "zigbee2mqtt"
MQTT_TOPICS = (
    "temp-and-humid",
    "motion",
)

MQTT_CLIENT_NAME = "Smart Hub"


def on_connect(client, user_data, flags, result_code):
    print(f"Connected to MQTT Broker - result code {result_code}")

    for topic in MQTT_TOPICS:
        subscribe_to = MQTT_BASE_TOPIC + "/" + topic + "/#"

        client.subscribe(subscribe_to)

        print(f"Subscribed to {subscribe_to}")


def on_message(client, data, message):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now} - [{message.topic}] ", str(message.payload.decode("utf-8")))


def on_subscribe(client, user_data, mid, granted_qos):
    print(f"Client: {client}")
    print(f"User_Data: {user_data}")
    print(f"Mid: {mid}")
    print(f"Granted_QOS: {granted_qos}")


client = mqtt.Client("Dummy_Device1")
client.on_connect = on_connect
client.on_message = on_message
# client.on_subscribe = on_subscribe

client.connect(MQTT_SERVER)


client.loop_forever()
