import datetime
from json.decoder import JSONDecodeError
import logging
import json
from django.core.management.base import CommandError
import paho.mqtt.client as mqtt

from django.core.management import BaseCommand

from ....devices.models import Device
from ...models import ZigbeeDevice, ZigbeeMessage, ZigbeeLog

logger = logging.getLogger("mqtt")
logger.setLevel(logging.INFO)
logging.basicConfig()

QOS = 1

MQTT_SERVER = "192.168.178.58"
MQTT_BASE_TOPIC = "zigbee2mqtt"
MQTT_TOPICS = ["#"]
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

        self.connect()

    def connect(self) -> None:
        self.client = mqtt.Client(self.client_name)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe

        self.client.connect(self.server)
        self.client.loop_forever()

    def on_connect(self, client, user_data, flags, result_code) -> None:
        logger.info(f"Connected to MQTT Broker - result code {result_code}")

        self.get_topics_for_subscribing()

        if self.subscribed_topics:
            client.subscribe(self.subscribed_topics)

    def on_message(self, client, data, message) -> None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        topic = message.topic
        payload = message.payload.decode("utf-8")

        logger.info(f"MQTT msg received: {now} - [{topic}] " + str(payload))
        MQTTMessage(topic=topic, payload=payload)

    def on_subscribe(self, client, user_data, mid, granted_qos) -> None:
        logger.info(f"MQTT subscribed to topics: {str(mid)} with QoS ({granted_qos})")

    def disconnect(self) -> None:
        self.client.disconnect()
        self.client = None
        logger.info("MQTT client ({connection.client_name}) disconnected")

    def get_topics_for_subscribing(self) -> None:
        topics_for_subscribing = []

        if not self.topics:
            logger.info("MQTT - no topics provided to subscribe to")
            return

        for topic in self.topics:
            new_topic = ""
            if self.base_topic:
                new_topic += self.base_topic + "/"
            new_topic += f"{topic}"

            topics_for_subscribing.append((new_topic, self.qos))

        self.subscribed_topics = topics_for_subscribing


class MQTTMessage:
    DEVICE_LIST_TOPIC = "zigbee2mqtt/bridge/devices"
    TOPIC_IGNORE_LIST = [
        "zigbee2mqtt/bridge/info",
    ]
    ZIGBEE_DEVICE_IDENTIFIER_FIELD = "ieee_address"

    topic = None
    raw_payload = None
    payload = None

    def __init__(self, topic, payload):
        self.topic = str(topic).strip()
        self.raw_payload = payload

        try:
            self.payload = json.loads(payload)

        except JSONDecodeError:
            return

        if self.topic in self.TOPIC_IGNORE_LIST:
            return

        if self.topic == self.DEVICE_LIST_TOPIC:
            self.parse_devices()
        else:
            self.parse_message()

    def parse_devices(self):
        current_devices = ZigbeeDevice.objects.all().values_list(
            self.ZIGBEE_DEVICE_IDENTIFIER_FIELD, flat=True
        )
        logger.info(f"current devices: {current_devices}")

        devices = self.payload
        logger.info(f"mqtt devices= {devices}")

        for device in devices:
            ieee_address = device.get("ieee_address")

            if not ieee_address in current_devices:
                new_device = ZigbeeDevice(user_device_model=Device)
                new_device = new_device.create_device(device)

                if new_device:
                    logger.info(f"MQTT - new device added - {new_device.ieee_address}")
                else:
                    logger.error(f"MQTT - could not create new device - data: {device}")

    def parse_message(self):
        payload = self.payload

        if isinstance(payload, list) and len(payload) > 0:
            payload = payload[0]

        zigbee_message = ZigbeeMessage(
            zigbee_device=None, raw_message=self.raw_payload, topic=self.topic
        )

        mqtt_data = payload

        if not zigbee_message:
            logger.error(
                f"MQTT - parse_message - could not record ZigbeeMessage - data: {mqtt_data}"
            )
            return

        zigbee_message.save()
        zigbee_device = zigbee_message.link_to_device_using_topic()
        zigbee_message.zigbee_device = zigbee_device

        if zigbee_device:
            logger.info(
                f"MQTT - message received for zigbee device ({zigbee_device.ieee_address})"
            )

        for field in mqtt_data:
            value = mqtt_data[field]

            if len(str(value)) > 0:
                log = ZigbeeLog(
                    broker_message=zigbee_message,
                    metadata_type=field,
                    metadata_value=value,
                )
                if not log:
                    logger.error(
                        f"MQTT - parse_message - could not record ZigbeeMessage - data: {mqtt_data}"
                    )
                log.save()

        logger.info("MQTT - parse_message - message successfully parsed")


class Command(BaseCommand):
    def handle(self, **options):
        connection = None
        try:
            connection = MQTTClient(
                MQTT_SERVER, MQTT_TOPICS, MQTT_CLIENT_NAME, QOS, MQTT_BASE_TOPIC
            )
            self.stdout.write(self.style.SUCCESS("MQTT client running"))
        except KeyboardInterrupt as ex:
            if connection:
                connection.disconnect()
            raise CommandError("MQTT connection closed")
