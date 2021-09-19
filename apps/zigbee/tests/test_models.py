from apps.events.models import EventResponse
from apps.users.tests.factories import UserFactory
from ...devices.models import DeviceProtocol
from ...devices.tests.factories import DeviceFactory
from django.test import TestCase
from .factories import ZigbeeDeviceFactory, ZigbeeLogFactory, ZigbeeMessageFactory
from ..models import ZigbeeDevice, ZigbeeMessage
from ...devices.tests.factories import ZigbeeDeviceStateFactory
from ...events.tests.factories import (
    EventTriggerFactory,
    EventResponseFactory,
    EventFactory,
)

import json

from unittest import mock


class TestZigbeeDevice(TestCase):
    def test_process_metadata_creates_device(self):
        metadata = {
            "type": "device_interview",
            "data": {
                "field": "something",
                "another-field": "another-something",
                "number": 1234,
                "ieee_address": "dummy-ieee-address",
            },
        }

        device = ZigbeeDevice.process_metadata(metadata=metadata)
        device_query = ZigbeeDevice.objects.filter(
            ieee_address="dummy-ieee-address"
        ).first()

        self.assertTrue(device is not None)
        self.assertEqual(ZigbeeDevice.objects.count(), 1)
        self.assertEqual(device.ieee_address, "dummy-ieee-address")
        self.assertEqual(device_query.ieee_address, "dummy-ieee-address")

    def test_process_metadata_does_not_create_device_when_no_ieee_address(self):
        metadata = {
            "type": "device_interview",
            "data": {
                "field": "something",
                "another-field": "another-something",
                "number": 1234,
            },
        }

        device = ZigbeeDevice.process_metadata(metadata=metadata)

        self.assertTrue(device is None)
        self.assertEqual(ZigbeeDevice.objects.count(), 0)

    def test_process_metadata_does_not_create_device_when_it_already_exists(self):
        zb_device = ZigbeeDeviceFactory()

        metadata = {
            "type": "device_interview",
            "data": {
                "field": "something",
                "another-field": "another-something",
                "number": 1234,
                "ieee_address": zb_device.ieee_address,
            },
        }

        device = ZigbeeDevice.process_metadata(metadata=metadata)

        self.assertTrue(device is None)
        self.assertEqual(ZigbeeDevice.objects.count(), 1)

    def test_create_device_does_not_create_object_when_no_metadata_provided(self):
        metadata = {}

        device = ZigbeeDevice.process_metadata(metadata=metadata)

        self.assertTrue(device is None)
        self.assertEqual(ZigbeeDevice.objects.count(), 0)

    def test_link_to_user_device_does_not_link_device_when_no_match_exists(self):
        metadata = {
            "type": "device_interview",
            "data": {
                "field": "something",
                "another-field": "another-something",
                "number": 1234,
                "ieee_address": "dummy-ieee-address",
            },
        }

        zb_device = ZigbeeDevice.process_metadata(metadata=metadata)
        device_query = ZigbeeDevice.objects.filter(
            ieee_address="dummy-ieee-address"
        ).first()

        self.assertEqual(zb_device, device_query)
        self.assertEqual(ZigbeeDevice.objects.count(), 1)
        self.assertFalse(zb_device.try_to_link_user_device())
        self.assertTrue(zb_device.device is None)

    def test_link_to_user_device_successful_using_ieee_address(self):
        zb_device = ZigbeeDeviceFactory(
            ieee_address="really-unique-address", device=None
        )
        user_device = DeviceFactory(protocol=DeviceProtocol.ZIGBEE)
        user_device.device_identifier = "really-unique-address"
        user_device.save(link_devices=False)

        self.assertTrue(zb_device.device is None)
        self.assertFalse(user_device.is_linked())

        self.assertTrue(zb_device.try_to_link_user_device())
        self.assertEqual(zb_device.device, user_device)

    def test_link_to_user_device_successful_using_friendly_name(self):
        zb_device = ZigbeeDeviceFactory(
            friendly_name="i-have-a-super-friendly-name", device=None
        )
        user_device = DeviceFactory(protocol=DeviceProtocol.ZIGBEE)
        user_device.friendly_name = "i-have-a-super-friendly-name"
        user_device.save(link_devices=False)

        self.assertTrue(zb_device.device is None)
        self.assertFalse(user_device.is_linked())

        self.assertTrue(zb_device.try_to_link_user_device())
        self.assertEqual(zb_device.device, user_device)

    def test_device_does_not_link_when_protocol_is_not_zigbee(self):
        zb_device = ZigbeeDeviceFactory(
            friendly_name="i-have-a-super-friendly-name", device=None
        )
        user_device = DeviceFactory(protocol=DeviceProtocol.API)
        user_device.friendly_name = "i-have-a-super-friendly-name"
        user_device.save(link_devices=False)

        self.assertFalse(zb_device.try_to_link_user_device())
        self.assertTrue(zb_device.device is None)
        self.assertFalse(user_device.is_linked())

    def test_user_device_returns_none_when_no_device(self):
        zb_device = ZigbeeDeviceFactory(device=None)

        self.assertTrue(zb_device.user_device is None)

    def test_user_device_returns_device(self):
        user_device = DeviceFactory(protocol=DeviceProtocol.ZIGBEE)
        zb_device = ZigbeeDeviceFactory(device=user_device)

        self.assertEqual(zb_device.user_device, user_device)


class TestZigbeeMessage(TestCase):
    def setUp(self) -> None:
        raw_msg = json.dumps(
            {
                "something-field1": "something-value",
                "something-field2": "something-value",
                "something-field3": "something-value",
            }
        )

        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user)
        self.zb_device = ZigbeeDeviceFactory(device=self.device)
        self.zb_msg = ZigbeeMessageFactory(
            zigbee_device=self.zb_device, raw_message=raw_msg
        )
        self.event = EventFactory(user=self.user, is_enabled=True)
        self.state = ZigbeeDeviceStateFactory(content_object=self.zb_device)
        self.response = EventResponse(
            event=self.event, device_state=self.state, is_enabled=True
        )

    @mock.patch("apps.zigbee.models.ZigbeeMessage.process_event_trigger")
    def test_check_event_triggers_successfully_triggered(self, mock_value):
        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
        ]

        self.zb_msg.check_event_triggers()
        total_trigger_calls = mock_value.call_count

        self.assertEqual(total_trigger_calls, len(triggers))

    @mock.patch("apps.zigbee.models.ZigbeeMessage.process_event_trigger")
    def test_check_event_triggers_not_called_when_disabled(self, mock_value):
        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=False),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=False),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
        ]

        self.zb_msg.check_event_triggers()
        total_trigger_calls = mock_value.call_count

        self.assertEqual(total_trigger_calls, 1)

    def test_process_event_trigger_device_value_has_changed_invoke_triggers(self):
        pass

    def test_process_event_trigger_device_value_has_changed_but_trigger_is_not_enabled(
        self,
    ):
        pass

    def test_process_event_trigger_device_value_has_not_changed_do_not_process(self):
        pass

    def test_process_event_trigger_records_a_trigger_log(self):
        pass

    def test_process_event_trigger_sends_notifications_when_enabled(self):
        pass

    def test_process_event_trigger_does_not_send_notifications_when_disabled(self):
        pass

    def test_invoke_event_response_returns_when_device_has_no_associated_user(self):
        pass

    def test_invoke_event_response_returns_when_device_has_no_event(self):
        pass

    def test_invoke_event_response_returns_when_device_has_no_event_responses(self):
        pass

    def test_invoke_event_response_successfully_sends_mqtt_messages(self):
        pass

    def test_invoke_notifications_successful_when_there_are_active_notifications(self):
        pass

    def test_invoke_notifications_returns_when_no_active_notifications(self):
        pass

    def test_invoke_notifications_sends_to_pushbullet_when_enabled(self):
        pass

    def test_invoke_notifications_sends_to_email_when_enabled(self):
        pass


class TestZigbeeLog(TestCase):
    def test_string_output(self):
        log = ZigbeeLogFactory()

        self.assertEqual(str(log), f"{log.metadata_type}={log.metadata_value}")
