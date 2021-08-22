"""Implements functionality for handling MQTT broker connections and messages"""
import datetime
import json
import logging
from json.decoder import JSONDecodeError
from random import random

from django.core import cache
from django.core.management import BaseCommand
from django.core.management.base import CommandError

import paho.mqtt.client as mqtt

from smarthub.settings import (
    MQTT_BASE_TOPIC,
    MQTT_CLIENT_NAME,
    MQTT_QOS,
    MQTT_SERVER,
    MQTT_TOPICS,
)

from ...models import ZigbeeDevice, ZigbeeLog, ZigbeeMessage

logger = logging.getLogger("mqtt")
logger.setLevel(logging.INFO)
logging.basicConfig()


class MQTTClient:
    """Handles connection to MQTT server and parsing all messages"""

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
        """Constructor captures required information for MQTT connection"""
        self.server = server
        self.topics = topics

        # if client disconnected without informing the server then server will not allow another
        # client to connect with the same name. To prevent a loop cycle, change name each
        # connection
        rand_num = int(random() * 1000)
        self.client_name = f"{client_name}-{rand_num}"
        self.qos = qos
        self.base_topic = base_topic

        self.connect()

    def connect(self) -> None:
        """Connects to MQTT broker and retains connection through loop"""
        try:
            self.client = mqtt.Client(self.client_name)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            self.client.on_disconnect = self.on_disconnect

            self.client.connect(self.server)
            self.client.loop_forever()
        except KeyboardInterrupt as ex:
            logger.info(ex)
            self.disconnect()

    def on_connect(self, client, user_data, flags, result_code) -> None:
        """Callback function - called when connection is successful"""
        logger.info("Connected to MQTT Broker")

        self.get_topics_for_subscribing()

        if self.subscribed_topics:
            client.subscribe(self.subscribed_topics)

    def on_message(self, client, data, message) -> None:
        """Callback function - called each time a message is received"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        topic = message.topic
        payload = message.payload.decode("utf-8")

        logger.info(f"MQTT msg received: {now} - [{topic}] " + str(payload))
        MQTTMessage(topic=topic, payload=payload)

    def on_subscribe(self, client, user_data, mid, granted_qos) -> None:
        """Callback function - called when MQTT subscribers have been successful"""
        logger.info(
            "MQTT subscribed to topics with guaranteed QoS level (%s)", granted_qos
        )

    def on_disconnect(self, client, userdata, rc):
        """Callback function - called when client disconnects from MQTT broker"""
        logger.info("MQTT client disconnected")

    def disconnect(self) -> None:
        """Disconnects from MQTT broker - manually invoked via Ctrl+C in terminal"""
        self.client.disconnect()
        self.client = None

    def get_topics_for_subscribing(self) -> None:
        """Returns list of topics used to subscribe to via MQTT broker"""
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
    """Handles storing and processing for messages received through MQTT topic subscriptions"""

    DEVICE_LIST_TOPIC = "zigbee2mqtt/bridge/devices"
    TOPIC_IGNORE_LIST = [
        "zigbee2mqtt/bridge/info",
        "zigbee2mqtt/bridge/logging",
        # "zigbee2mqtt/bridge/devices",
        "zigbee2mqtt/bridge/groups",
        # "zigbee2mqtt/bridge/config",
    ]
    ZIGBEE_DEVICE_IDENTIFIER_FIELD = "ieee_address"

    topic = None
    raw_payload = None
    parsed_payload = None

    def __init__(self, topic, payload):
        """Constructor"""
        self.topic = str(topic).strip().lower()
        self.raw_payload = payload

        try:
            self.parsed_payload = json.loads(payload)

        except JSONDecodeError:
            return

        if self.topic in self.TOPIC_IGNORE_LIST:
            return

        if self.topic == self.DEVICE_LIST_TOPIC:
            self.parse_devices()
        else:
            self.parse_message()

    def parse_devices(self):
        """Loops through devices listed by MQTT broker and creates ZigbeeDevice objects for those
        that don't already exist in the DB."""
        current_devices = ZigbeeDevice.objects.all().values_list(
            self.ZIGBEE_DEVICE_IDENTIFIER_FIELD, flat=True
        )
        devices = self.parsed_payload

        for device in devices:
            ieee_address = device.get("ieee_address")

            if not ieee_address in current_devices:
                try:
                    new_device = ZigbeeDevice.create_device(device)

                    logger.info("MQTT - new device added - %s",
                                new_device.ieee_address)
                except Exception as ex:
                    logger.error(
                        "Exception creating new Zigbee Device (%s) %s", device, ex
                    )
            else:
                logger.info("Device already exists [%s]", ieee_address)

    def parse_message(self):
        """Parses MQTT messages - linking to a ZigbeeDevice (if possible) - and
        retains message content in DB.

        Messages are stored in two distinct objects - ZigbeeMessage and ZigbeeLog.

        ZigbeeMessage - this is a raw copy of the message received.
        ZigbeeLog - the raw message is parsed, creating a record for each metadata field with
                    associated value. This is useful for dynamically providing trigger options
                    for each Device."""
        payload = self.parsed_payload

        if isinstance(payload, list) and len(payload) > 0:
            payload = payload[0]

        try:

            # make sure message does not already exist first - MQTT devices rebroadcast if
            # it is not aware that the message has been received
            existing_messages = ZigbeeMessage.objects.filter(
                raw_message=self.raw_payload
            ).count()

            if existing_messages > 0:
                logger.info("Duplicate message - ignoring")
                return

            zigbee_message = ZigbeeMessage(
                zigbee_device=None, raw_message=self.raw_payload, topic=self.topic
            )

            mqtt_data = payload

            if not zigbee_message:
                logger.error(
                    "MQTT - parse_message - could not record ZigbeeMessage - data: %s",
                    mqtt_data,
                )
                return

            # updates zigbeedevice field and saves object
            zigbee_message.save()

            # TODO - add caching for latest values
            # TODO - use latest cache values to check if notification should be invoked (i.e. has it changed)
            # TODO - possibly set cache value for notify_user=True (if falls outside notification criteria) & False if it stays in criteria range
            for field in mqtt_data:
                field = str(field).lower()
                value = mqtt_data[field]

                if len(str(value)) > 0:
                    log = ZigbeeLog(
                        broker_message=zigbee_message,
                        metadata_type=field,
                        metadata_value=value,
                    )
                    if not log:
                        logger.error(
                            "MQTT - parse_message - could not record ZigbeeMessage - data: %s",
                            mqtt_data,
                        )
                    log.save()

            logger.info("MQTT - parse_message - message successfully parsed")

        except Exception as ex:
            logger.error("Encountered an error creating ZigbeeMessage: %s", ex)


class Command(BaseCommand):
    """Implements Django management class required functionality to enable MQTT to be
    run from terminal"""

    def handle(self, *args, **options):
        try:
            MQTTClient(
                MQTT_SERVER, MQTT_TOPICS, MQTT_CLIENT_NAME, MQTT_QOS, MQTT_BASE_TOPIC
            )
        except Exception:
            raise CommandError("MQTT connection closed")
