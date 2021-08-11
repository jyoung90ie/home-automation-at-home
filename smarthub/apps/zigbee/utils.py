import datetime
import logging
import asyncio
import uuid
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

QOS = 1

MQTT_SERVER = "192.168.178.58"
MQTT_BASE_TOPIC = "zigbee2mqtt"
MQTT_TOPICS = [
    "temp-and-humid",
    "motion",
]
MQTT_CLIENT_NAME = "Smart Hub"


class MQTTClient:
    client = None
    subscribed_topics = None

    def __init__(
        self,
        server: str,
        topics: list,
        client_name: str,
        qos: int,
        base_topic: str = "",
    ) -> None:
        self.server = server
        self.topics = topics
        self.client_name = client_name
        self.qos = qos
        self.base_topic = base_topic

    def connect(self) -> None:
        self.client = mqtt.Client(self.client_name)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe

        self.client.connect(self.server)
        self.client.loop_forever()

    def on_connect(self, client, user_data, flags, result_code) -> None:
        print(f"Connected to MQTT Broker - result code {result_code}")

        self.get_topics_for_subscribing()

        if self.subscribed_topics:
            client.subscribe(self.subscribed_topics)

    def on_message(self, client, data, message) -> None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{now} - [{message.topic}] ", str(message.payload.decode("utf-8")))

    def on_subscribe(self, client, user_data, mid, granted_qos) -> None:
        print(f"Client: {client}")
        print(f"User_Data: {user_data}")
        print(f"Mid: {mid}")
        print(f"Granted_QOS: {granted_qos}")

    def disconnect(self) -> None:
        self.client.disconnect()
        self.client = None
        print(f"Client {connection.client_name} disconnected")

    def get_topics_for_subscribing(self) -> None:
        topics_for_subscribing = []

        if not self.topics:
            print("No topics provided - nothing to subscribe to")

        for topic in self.topics:
            new_topic = ""
            if self.base_topic:
                new_topic += self.base_topic + "/"
            new_topic += f"{topic}/#"

            topics_for_subscribing.append((new_topic, self.qos))

        self.subscribed_topics = topics_for_subscribing


if __name__ == "__main__":
    connection = None
    try:
        connection = MQTTClient(
            MQTT_SERVER, MQTT_TOPICS, MQTT_CLIENT_NAME, QOS, MQTT_BASE_TOPIC
        )
        connection.connect()
    except KeyboardInterrupt as ex:
        connection.disconnect()
