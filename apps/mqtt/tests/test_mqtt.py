import json
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from ...zigbee.models import ZigbeeDevice, ZigbeeLog, ZigbeeMessage
from ...zigbee.tests.factories import ZigbeeDeviceFactory
from ..management.commands.mqtt import (MQTTClient, MQTTMessage,
                                        has_message_sufficiently_changed,
                                        parse_message_for_comparison)
from ..utils import get_cache_key


class TestParseMessageForComparison(TestCase):
    def setUp(self):
        self.valid_message = json.dumps(
            {
                "dummy_field_1": "2021-09-19T12:11:43+01:00",
                "dummy_field_2": "Something",
                "dummy_field_3": 95,
                "dummy_field_4": 75.4,
                "dummy_field_5": "OFF",
            }
        )
        self.ignored_fields = [
            "dummy_field_1",
            "dummy_field_3",
            "dummy_field_5",
        ]

    @mock.patch(
        "apps.mqtt.management.commands.mqtt.defines",
        autospec=True,
    )
    def test_that_ignored_fields_are_removed(self, mock_ignored):
        mock_ignored.MESSAGE_FIELDS_TO_IGNORE = self.ignored_fields

        parsed_message = parse_message_for_comparison(self.valid_message)

        for ignored in self.ignored_fields:
            with self.subTest(ignored=ignored):
                self.assertNotIn(ignored, parsed_message)

        self.assertNotEqual(parsed_message, self.valid_message)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class TestHasMessageSufficientlyChanged(TestCase):
    @mock.patch(
        "apps.mqtt.management.commands.mqtt.defines",
        autospec=True,
    )
    def setUp(self, mock_ignored):
        self.ignored_fields = [
            "dummy_field_1",
            "dummy_field_3",
            "dummy_field_5",
        ]

        mock_ignored.MESSAGE_FIELDS_TO_IGNORE = self.ignored_fields

        self.cache_key = get_cache_key("dummy_identifier_1")

        self.message = json.dumps(
            {
                "dummy_field_1": "2021-09-19T12:11:43+01:00",
                "dummy_field_2": "Something",
                "dummy_field_3": 95,
                "dummy_field_4": 75.4,
                "dummy_field_5": "OFF",
            }
        )

        # call to create cache for message
        has_message_sufficiently_changed(message=self.message, cache_key=self.cache_key)

    def test_when_message_is_unchanged_returns_false(self):
        self.assertFalse(
            has_message_sufficiently_changed(
                message=self.message, cache_key=self.cache_key
            )
        )

    @mock.patch(
        "apps.mqtt.management.commands.mqtt.defines",
        autospec=True,
    )
    def test_when_only_ignored_fields_have_changed_returns_false_and_cache_updated(
        self, mock_ignored
    ):
        mock_ignored.MESSAGE_FIELDS_TO_IGNORE = self.ignored_fields
        message = json.dumps(
            {
                "dummy_field_1": "ignored-field",  # changed
                "dummy_field_2": "Something",
                "dummy_field_3": "ignored-field",  # changed
                "dummy_field_4": 75.4,
                "dummy_field_5": "ignored-field",  # changed
            }
        )

        self.assertFalse(
            has_message_sufficiently_changed(message=message, cache_key=self.cache_key)
        )
        self.assertEqual(message, cache.get(self.cache_key))

    @mock.patch(
        "apps.mqtt.management.commands.mqtt.defines",
        autospec=True,
    )
    def test_when_non_ignored_field_changes_returns_true_and_cache_updated(
        self, mock_ignored
    ):
        mock_ignored.MESSAGE_FIELDS_TO_IGNORE = self.ignored_fields
        message = json.dumps(
            {
                "dummy_field_1": "2021-09-19T12:11:43+01:00",
                "dummy_field_2": "Something-Else",  # changed
                "dummy_field_3": 95,
                "dummy_field_4": 75.4,
                "dummy_field_5": "OFF",
            }
        )

        self.assertTrue(
            has_message_sufficiently_changed(message=message, cache_key=self.cache_key)
        )
        self.assertEqual(message, cache.get(self.cache_key))


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class TestMQTTMessage(TestCase):
    def setUp(self):
        self.devices_payload = json.dumps(
            [
                {
                    "ieee_address": "dummy-ieee-address-1",
                },
                {
                    "ieee_address": "dummy-ieee-address-2",
                },
                {
                    "ieee_address": "dummy-ieee-address-3",
                },
            ]
        )

    def test_raw_payload_is_parsed_from_json_string(self):
        topic = "test/topic"
        raw_payload = json.dumps({"data": {"test": 1234}})

        mqtt_msg = MQTTMessage(topic=topic, payload=raw_payload)

        self.assertEqual(mqtt_msg.parsed_payload, json.loads(raw_payload))

    def test_invalid_json_string_payload_does_not_through_error(self):
        topic = "test/topic"
        raw_payload = """{"data": {"test": 1234, something: "error"}}"""

        mqtt_msg = MQTTMessage(topic=topic, payload=raw_payload)
        self.assertTrue(mqtt_msg.parsed_payload is None)

    @mock.patch(
        "apps.mqtt.management.commands.mqtt.defines",
        autospec=True,
    )
    def test_parse_devices_creates_new_devices(self, mock_device_topic):
        topic = "devices"

        mock_device_topic.MQTT_DEVICE_LIST_TOPIC = topic
        mock_device_topic.ZIGBEE_DEVICE_IDENTIFIER_FIELD = "ieee_address"

        zigbee_devices = ZigbeeDevice.objects.all()
        total_devices = zigbee_devices.count()
        self.assertEqual(total_devices, 0)

        MQTTMessage(topic=topic, payload=self.devices_payload)

        new_total = zigbee_devices.count()
        self.assertEqual(new_total, 3)

    @mock.patch(
        "apps.mqtt.management.commands.mqtt.defines",
        autospec=True,
    )
    def test_parse_devices_only_creates_devices_when_they_dont_exist(
        self, mock_device_topic
    ):
        ZigbeeDeviceFactory(device=None, ieee_address="dummy-ieee-address-1")

        topic = "devices"

        mock_device_topic.MQTT_DEVICE_LIST_TOPIC = topic
        mock_device_topic.ZIGBEE_DEVICE_IDENTIFIER_FIELD = "ieee_address"

        zigbee_devices = ZigbeeDevice.objects.all()
        total_devices = zigbee_devices.count()
        self.assertEqual(total_devices, 1)

        MQTTMessage(topic=topic, payload=self.devices_payload)

        new_total = zigbee_devices.count()
        self.assertEqual(new_total, 3)
        self.assertTrue(
            zigbee_devices.filter(ieee_address="dummy-ieee-address-1").first()
            is not None
        )
        self.assertTrue(
            zigbee_devices.filter(ieee_address="dummy-ieee-address-2").first()
            is not None
        )
        self.assertTrue(
            zigbee_devices.filter(ieee_address="dummy-ieee-address-3").first()
            is not None
        )

    @mock.patch(
        "apps.mqtt.management.commands.mqtt.defines",
        autospec=True,
    )
    def test_device_attributes_correctly_parsed(self, mock_device_topic):
        topic = "devices"

        device_payload = json.dumps(
            [
                {
                    "definition": {
                        "description": "A wonderful test device used for...testing!",
                        "model": "DUMMY 321",
                        "vendor": "DUMMY VENDOR",
                        "not-a-real-field": "fakefake",
                    },
                    "friendly_name": "DUMMY-FRIENDLY-NAME",
                    "ieee_address": "dummy-ieee-address",
                    "interview_completed": True,
                    "interviewing": False,
                    "model_id": "DUMMY123",
                    "network_address": 60801,
                    "power_source": "Dummy-Mains",
                    "supported": True,
                    "type": "Router",
                },
            ]
        )

        mock_device_topic.MQTT_DEVICE_LIST_TOPIC = topic
        mock_device_topic.ZIGBEE_DEVICE_IDENTIFIER_FIELD = "ieee_address"

        MQTTMessage(topic=topic, payload=device_payload)

        zb_device = ZigbeeDevice.objects.get(ieee_address="dummy-ieee-address")
        self.assertTrue(zb_device is not None)
        self.assertEqual(zb_device.friendly_name, "dummy-friendly-name")
        self.assertEqual(
            zb_device.description, "A wonderful test device used for...testing!"
        )
        self.assertEqual(zb_device.vendor, "DUMMY VENDOR")
        self.assertEqual(zb_device.model, "DUMMY 321")
        self.assertEqual(zb_device.model_id, "DUMMY123")
        self.assertEqual(zb_device.power_source, "Dummy-Mains")
        self.assertEqual(zb_device.is_controllable, False)
        self.assertEqual(zb_device.device, None)
        self.assertEqual(zb_device.device_states.first(), None)

    @mock.patch(
        "apps.mqtt.management.commands.mqtt.defines",
        autospec=True,
    )
    def test_device_states_correctly_parsed(self, mock_device_topic):
        topic = "devices"

        device_payload = json.dumps(
            [
                {
                    "definition": {
                        "exposes": [
                            {
                                "features": [
                                    {
                                        "access": 12345,
                                        "description": "Turn it on or off",
                                        "name": "state",
                                        "property": "state",
                                        "type": "binary",
                                        "value_off": "OFF",
                                        "value_on": "ON",
                                        "value_toggle": "TOGGLE",
                                    }
                                ],
                                "type": "switch",
                            },
                        ],
                    },
                    "ieee_address": "dummy-ieee-address",
                },
            ]
        )

        mock_device_topic.MQTT_DEVICE_LIST_TOPIC = topic
        mock_device_topic.ZIGBEE_DEVICE_IDENTIFIER_FIELD = "ieee_address"

        MQTTMessage(topic=topic, payload=device_payload)

        zb_device = ZigbeeDevice.objects.get(ieee_address="dummy-ieee-address")
        self.assertTrue(zb_device is not None)
        self.assertEqual(zb_device.device_states.count(), 3)

        zb_device_states = zb_device.device_states.all()
        # values are transformed to lower case
        self.assertTrue(
            zb_device_states.filter(
                name="OFF", command="state", command_value="off"
            ).exists()
        )
        self.assertTrue(
            zb_device_states.filter(
                name="ON", command="state", command_value="on"
            ).exists()
        )
        self.assertTrue(
            zb_device_states.filter(
                name="TOGGLE", command="state", command_value="toggle"
            ).exists()
        )

    def test_empty_payload(self):
        topic = "something-something"
        raw_payload = ""

        mqtt_msg = MQTTMessage(topic=topic, payload=raw_payload)

        self.assertEqual(mqtt_msg.topic, None)
        self.assertEqual(mqtt_msg.raw_payload, None)
        self.assertEqual(mqtt_msg.parsed_payload, None)

    def test_parse_message(self):
        zb_device = ZigbeeDevice(device=None, ieee_address="dummy-ieee-address")

        topic = "dummy-ieee-address"
        device_message = json.dumps(
            {
                "some_field": "some value",
                "another_field": "another value",
                "a_number_field": 1234,
            }
        )

        mqtt_msg = MQTTMessage(topic=topic, payload=device_message)

        zb_message = ZigbeeMessage.objects.filter(zigbee_device=zb_device)
        zb_logs = ZigbeeLog.objects.filter(broker_message=zb_message.first())

        self.assertEqual(zb_message.count(), 1)
        self.assertEqual(zb_logs.count(), 3)
        self.assertTrue(
            zb_logs.filter(
                metadata_type="some_field", metadata_value="some value"
            ).exists()
        )
        self.assertTrue(
            zb_logs.filter(
                metadata_type="another_field", metadata_value="another value"
            ).exists()
        )
        self.assertTrue(
            zb_logs.filter(metadata_type="a_number_field", metadata_value=1234).exists()
        )

    @mock.patch(
        "apps.mqtt.management.commands.mqtt.defines",
        autospec=True,
    )
    def test_that_message_is_not_parsed_when_published_to_ignored_topic(
        self, mock_device_topic
    ):
        topic = "ignored"
        mock_device_topic.MQTT_TOPIC_IGNORE_LIST = topic

        zb_device = ZigbeeDevice(device=None, ieee_address="dummy-ieee-address")

        device_message = json.dumps(
            {
                "some_field": "some value",
                "another_field": "another value",
                "a_number_field": 1234,
            }
        )

        MQTTMessage(topic=topic, payload=device_message)

        zb_message = ZigbeeMessage.objects.filter(zigbee_device=zb_device)
        zb_logs = ZigbeeLog.objects.filter(broker_message=zb_message.first())

        self.assertEqual(zb_message.count(), 0)
        self.assertEqual(zb_logs.count(), 0)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class TestMQTTClient(TestCase):
    def setUp(self):
        pass
