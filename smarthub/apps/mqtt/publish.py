"""Creates an MQTT client, publishes a message, and closes connection"""
import datetime
import json
import logging
from random import random

import paho.mqtt.client as mqtt

# from smarthub.settings import (
#     MQTT_BASE_TOPIC,
#     MQTT_CLIENT_NAME,
#     MQTT_QOS,
#     MQTT_SERVER,
# )

logger = logging.getLogger("mqtt")
logger.setLevel(level=logging.INFO)
logging.basicConfig()


# PUBLISH_CLIENT_NAME = MQTT_CLIENT_NAME + " - Publisher"


class MQTTPublish:
    """Connects to MQTT broker, publishes message, and disconnects"""

    client = None

    def __init__(
        self,
        server: str,
        topic: str,
        message: str,
        qos: int,
    ) -> None:
        """Constructor captures required information for MQTT connection"""
        self.server = server
        self.topic = topic
        self.message = message

        # if client disconnected without informing the server then server will not allow another
        # client to connect with the same name. To prevent a loop cycle, change name each
        # connection
        rand_num = int(random() * 1000)
        self.client_name = f"Smart Hub-{rand_num}"
        self.qos = qos

        self.connect()

    def connect(self) -> None:
        """Connects to MQTT broker and retains connection through loop"""
        try:
            self.client = mqtt.Client(self.client_name)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish

            self.client.connect(self.server)
            self.client.loop_forever()
        except Exception as ex:
            logger.info(ex)
            self.disconnect()

    def on_connect(
        self, client, user_data, flags, result_code, properties=None
    ) -> None:
        """Called when client connects to broker"""
        if result_code == 0:
            logger.info("Connected to MQTT Broker")

            # TODO - publish message here
            self.publish(topic=self.topic, payload=self.message, qos=self.qos)

        else:
            logger.error("Could not connect to MQTT broker")

    def on_publish(self, client, user_data, mid):
        logger.info("Message published - can disconnect now")
        logger.info("User Data: %s, Mid: %s", user_data, mid)
        self.disconnect()

    def publish(self, topic, payload, qos=1, retain=False, properties=None):
        """Send messages to MQTT broker"""
        self.client.publish(topic, payload, qos, retain, properties)

    def on_message(self, client, user_data, message) -> None:
        """Callback function - called each time a message is received"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        topic = message.topic
        payload = message.payload.decode("utf-8")

        logger.info("MQTT msg received: %s - [%s] %s", now, topic, str(payload))

    def on_disconnect(self, client, user_data, result_code):
        """Callback function - called when client disconnects from MQTT broker"""
        logger.info("MQTT client disconnected")

    def disconnect(self) -> None:
        """Disconnects from MQTT broker - manually invoked via Ctrl+C in terminal"""
        self.client.disconnect()
        self.client = None


if __name__ == "__main__":
    server = "192.168.178.58"
    topic = "zigbee2mqtt/0x84fd27fffe922027/set"
    message = {"state": "TOGGLE"}
    message = json.dumps(message)
    MQTTPublish(server=server, topic=topic, message=message, qos=1)
