"""Implements functionality for handling MQTT broker connections and messages"""
import datetime
import json
import logging
from json.decoder import JSONDecodeError
from random import random
from typing import Union

from django.core.cache import cache
from django.core.management import BaseCommand
from django.core.management.base import CommandError

import paho.mqtt.client as mqtt

from smarthub.settings import (MQTT_BASE_TOPIC, MQTT_CLIENT_NAME, MQTT_QOS,
                               MQTT_SERVER, MQTT_TOPICS)

from ....devices.models import DeviceState
from ....zigbee.models import ZigbeeDevice, ZigbeeLog, ZigbeeMessage
from ... import defines
from ...utils import get_cache_key

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
logging.basicConfig()


def parse_message_for_comparison(
    message: str, is_cache: bool = False
) -> Union["str", "None"]:
    """Parses the MQTT message, comparing the content against that stored in the cache.
    Importantly, it ignores all fields list in MESSAGE_FIELDS_TO_IGNORE as these are deemed to
    have immaterial value in terms of triggering events.

    This ensures that when comparing message content, only the important fields can invoke
    an event.

    Parameters:
        message:    raw MQTT message
        is_cache:   is this a cached message - if so, turn off log message to avoid duplication
    """
    if not message:
        return None

    try:

        json_message = json.loads(message)

        parsed_message = {}

        for field in json_message:
            if field in defines.MESSAGE_FIELDS_TO_IGNORE:
                continue  # ignore

            parsed_message[field] = json_message[field]

        if not is_cache:
            logger.info("Parsed message %s", parsed_message)
        return json.dumps(parsed_message)
    except JSONDecodeError:
        logger.debug("Could not parse message %s - is_cache=%s", message, is_cache)
        return None


def has_message_sufficiently_changed(message: str, cache_key: str) -> bool:
    """Compares the message against the last cached message to see if it has changed -
    excluding ignored fields. This helps prevent event triggers when a device rebroadcasts a
    message, with little to no content change."""

    cache_data = cache.get(key=cache_key)
    has_changed = True

    if cache_data:
        # parsing both messages so that the raw message is retained in cache for debugging if needed
        parsed_message = parse_message_for_comparison(message=message)
        parsed_cache = parse_message_for_comparison(message=cache_data, is_cache=True)

        if parsed_message == parsed_cache:
            logger.info("Message content unchanged - skipping event triggers")
            has_changed = False

    # device has no message or message is different from cached value
    if has_changed:
        logger.info("Message content changed")

    cache.set(key=cache_key, value=message, timeout=None)
    return has_changed


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
        self.qos = int(qos)
        self.base_topic = str(base_topic)

        # if client disconnected without informing the server then server will not allow another
        # client to connect with the same name. To prevent a loop cycle, change name each
        # connection
        rand_num = int(random() * 1000)
        self.client_name = f"{str(client_name)}-{rand_num}"

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
        except Exception as ex:
            logger.error("Could not connect to MQTT broker - %s", ex)
            logger.info(
                "Server - QOS: %s - Address: %s - Base Topic: %s - Client Name: %s",
                MQTT_QOS,
                MQTT_SERVER,
                MQTT_BASE_TOPIC,
                MQTT_CLIENT_NAME,
            )

    def on_connect(self, client, user_data, flags, result_code) -> None:
        """Callback function - called when connection is successful"""
        if result_code == 0:
            logger.info("Connected to MQTT Broker")
            try:

                self.get_topics_for_subscribing()

                if self.subscribed_topics:
                    client.subscribe(self.subscribed_topics)
            except Exception as ex:
                logger.error("Could not subscribe to topics - %s", ex)
        else:
            logger.error(
                "Could not connect to MQTT broker - result_code was different from 0"
            )

    def on_message(self, client, user_data, message) -> None:
        """Callback function - called each time a message is received"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            topic = message.topic
            payload = message.payload.decode("utf-8")

            logger.info("MQTT msg received: %s - [%s] %s", now, topic, str(payload))
            MQTTMessage(topic=topic, payload=payload)
        except Exception as ex:
            logger.debug("There was a problem parsing MQTT message - %s", ex)

    def on_subscribe(self, client, user_data, mid, qos) -> None:
        """Callback function - called when MQTT subscribers have been successful"""
        logger.info("MQTT subscribed to topics with guaranteed QoS level (%s)", qos)

    def on_disconnect(self, client, user_data, result_code):
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
            new_topic += topic

            topics_for_subscribing.append((new_topic, self.qos))

        self.subscribed_topics = topics_for_subscribing


class MQTTMessage:
    """Handles storing and processing for messages received through MQTT topic subscriptions"""

    topic = None
    raw_payload = None
    parsed_payload = None

    def __init__(self, topic: str, payload: str) -> None:
        """Constructor"""
        if len(payload) == 0:
            logger.debug("MQTT Message - payload empty - ignored")
            return

        self.topic = str(topic).strip().lower()
        self.raw_payload = payload

        try:
            self.parsed_payload = json.loads(payload)
        except JSONDecodeError as ex:
            logger.error(
                "MQTT Messsage - could not process payload - %s - %s", ex, payload
            )
            return

        if self.topic == defines.MQTT_DEVICE_LIST_TOPIC:
            self.parse_devices()  # also parses capabilities
        elif self.topic in defines.MQTT_TOPIC_IGNORE_LIST:
            logger.info(
                "MQTT - msg received on an ignored topic '%s' - msg ignored", self.topic
            )
            return
        else:
            self.parse_message()

    def parse_devices(self):
        """Loops through devices listed by MQTT broker and creates ZigbeeDevice objects for those
        that don't already exist in the DB."""
        current_devices = ZigbeeDevice.objects.all().values_list(
            defines.ZIGBEE_DEVICE_IDENTIFIER_FIELD, flat=True
        )
        devices = self.parsed_payload

        for device in devices:
            ieee_address = device.get("ieee_address")

            if not ieee_address in current_devices:
                try:
                    new_device = ZigbeeDevice.create_device(device)

                    logger.info("MQTT - new device added - %s", new_device.ieee_address)

                    self.parse_device_attributes(
                        zb_device=new_device, device_data=device
                    )
                except Exception as ex:
                    logger.error(
                        "Exception creating new Zigbee Device (%s) %s", device, ex
                    )
            else:
                logger.info(
                    "Device already exists - %s",
                    ieee_address,
                )

    def parse_device_attributes(
        self, zb_device: "ZigbeeDevice", device_data: dict
    ) -> None:
        """Parses device capabilities - this will determine whether a device can be controlled
        or is a sensor"""
        logger.info("Checking device attributes for - %s", zb_device)

        definitions = device_data.get("definition", None)

        if definitions:
            attributes = definitions.get("exposes")

            for attribute in attributes:
                features = attribute.get("features")

                if features:
                    logger.info("Found attributes for - %s", zb_device)
                    for feature in features:
                        state_command = feature.get("property")
                        value_on = feature.get("value_on")
                        value_off = feature.get("value_off")
                        value_toggle = feature.get("value_toggle")

                        if state_command:
                            logger.info(
                                "Updating device field `is_controllable` - %s",
                                zb_device,
                            )
                            zb_device.is_controllable = True
                            zb_device.save()

                            command_values = [value_off, value_on, value_toggle]

                            for cmd_val in command_values:
                                if not cmd_val:
                                    continue

                                if zb_device.device_states.filter(name=cmd_val).first():
                                    logger.info(
                                        "Device state already exists [%s=%s] - %s",
                                        state_command,
                                        cmd_val,
                                        zb_device,
                                    )
                                    continue

                                logger.info(
                                    "Adding device state [%s=%s] - %s",
                                    state_command,
                                    cmd_val,
                                    zb_device,
                                )
                                try:
                                    DeviceState.objects.create(
                                        content_object=zb_device,
                                        name=cmd_val,
                                        command=state_command,
                                        command_value=cmd_val,
                                    )
                                    logger.info("DeviceState created - %s", zb_device)
                                except Exception as ex:
                                    logger.info(ex)
        logger.info("Finished parsing device attributes...")

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
                    "%s - parse_message - could not record ZigbeeMessage - data: %s",
                    __name__,
                    mqtt_data,
                )
                return

            cache_key = get_cache_key(device_identifier=self.topic)
            # take a copy of the last cache value and pass it through for comparison
            last_message = cache.get(cache_key, "")

            has_message_changed = has_message_sufficiently_changed(
                message=self.raw_payload, cache_key=cache_key
            )
            logger.info("%s - Creating ZigbeeMessage: %s", __name__, zigbee_message)

            # updates zigbeedevice field and saves object
            try:
                zigbee_message.save(
                    check_triggers=has_message_changed, last_message=last_message
                )
            except Exception as ex:
                logger.info("Could not create ZigbeeMessage - %s", ex)

            logger.info("%s - ZigbeeMessage saved", __name__)

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
                            "%s - parse_message - could not record ZigbeeMessage - data: %s",
                            __name__,
                            mqtt_data,
                        )
                    log.save()

            logger.info("%s - parse_message - message successfully parsed", __name__)

        except Exception as ex:
            logger.error(
                "%s - Encountered an error creating ZigbeeMessage: %s", __name__, ex
            )


class Command(BaseCommand):
    """Implements Django management class required functionality to enable MQTT to be
    run from terminal"""

    def handle(self, *args, **options):
        try:
            MQTTClient(
                MQTT_SERVER, MQTT_TOPICS, MQTT_CLIENT_NAME, MQTT_QOS, MQTT_BASE_TOPIC
            )
        except Exception:
            CommandError("MQTT connection closed")
