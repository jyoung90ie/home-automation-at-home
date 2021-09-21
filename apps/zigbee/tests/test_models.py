import json
from unittest import mock

from django.test import TestCase

from ...devices.models import DeviceProtocol
from ...devices.tests.factories import DeviceFactory, ZigbeeDeviceStateFactory
from ...events.models import EventResponse, EventTriggerLog
from ...events.tests.factories import (
    EventFactory,
    EventResponseFactory,
    EventTriggerFactory,
)
from ...notifications.models import NotificationMedium
from ...notifications.tests.factories import (
    EmailNotificationFactory,
    NotificationSettingFactory,
    PushbulletNotificationFactory,
)
from ...users.tests.factories import UserFactory
from ..models import ZigbeeDevice, ZigbeeMessage
from .factories import ZigbeeDeviceFactory, ZigbeeLogFactory, ZigbeeMessageFactory


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
        self.event = EventFactory(
            user=self.user, is_enabled=True, send_notification=True
        )
        self.state = ZigbeeDeviceStateFactory(content_object=self.zb_device)
        self.response = EventResponseFactory(
            event=self.event, device_state=self.state, is_enabled=True
        )

    @mock.patch(
        "apps.zigbee.models.ZigbeeMessage.process_event_trigger",
        return_value=(True, True),
    )
    def test_check_event_triggers_successfully_triggered(self, mock_value):
        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
        ]

        self.zb_msg.check_event_triggers()
        total_trigger_calls = mock_value.call_count

        self.assertEqual(total_trigger_calls, len(triggers))

    @mock.patch(
        "apps.zigbee.models.ZigbeeMessage.process_event_trigger",
        return_value=(True, True),
    )
    def test_check_event_triggers_not_called_when_disabled(self, mock_value):
        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=False),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=False),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
        ]

        self.zb_msg.check_event_triggers()
        total_trigger_calls = mock_value.call_count

        self.assertEqual(total_trigger_calls, 1)

    @mock.patch("apps.events.models.EventTrigger.is_triggered", return_value=True)
    @mock.patch("apps.zigbee.models.ZigbeeMessage.invoke_event_response", autospec=True)
    def test_process_event_trigger_invokes_event_response_when_device_is_triggered(
        self, mock_invoke_response, mock_triggered
    ):

        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
        ]

        self.zb_msg.check_event_triggers()
        total_trigger_calls = mock_invoke_response.call_count

        self.assertEqual(total_trigger_calls, 3)

    @mock.patch("apps.events.models.EventTrigger.is_triggered", return_value=False)
    @mock.patch("apps.zigbee.models.ZigbeeMessage.invoke_event_response", autospec=True)
    def test_invoke_event_response_is_not_called_when_event_is_not_triggered(
        self, mock_invoke_response, mock_triggered
    ):

        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
        ]

        self.zb_msg.check_event_triggers()
        total_trigger_calls = mock_invoke_response.call_count

        self.assertEqual(total_trigger_calls, 0)

    @mock.patch("apps.events.models.EventTrigger.is_triggered")
    @mock.patch(
        "apps.zigbee.models.ZigbeeMessage.invoke_notifications",
    )
    def test_that_notifications_are_only_called_once_per_event(
        self, mock_invoke_notification, mock_triggered
    ):
        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
        ]
        self.zb_msg.check_event_triggers()

        total_trigger_calls = mock_invoke_notification.call_count

        self.assertEqual(total_trigger_calls, 1)

    @mock.patch(
        "apps.zigbee.models.ZigbeeMessage.process_event_trigger",
    )
    def test_does_not_call_process_event_trigger_when_event_is_disabled(
        self, mock_value
    ):
        self.event.is_enabled = False
        self.event.save()

        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
        ]

        self.zb_msg.check_event_triggers()
        total_trigger_calls = mock_value.call_count

        self.assertEqual(total_trigger_calls, 0)

    @mock.patch("apps.zigbee.models.ZigbeeMessage.process_event_trigger")
    @mock.patch("apps.events.models.Event", autospec=True)
    def test_does_not_call_process_event_trigger_when_event_triggers_are_disabled(
        self, mock_event, mock_value
    ):
        mock_event.is_enabled.return_value = True

        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=False),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=False),
        ]

        self.zb_msg.check_event_triggers()
        total_trigger_calls = mock_value.call_count

        self.assertEqual(total_trigger_calls, 0)

    @mock.patch("apps.events.models.Event.is_enabled", return_value=True)
    @mock.patch(
        "apps.zigbee.models.ZigbeeMessage.device_value_changed", return_value=False
    )
    @mock.patch("apps.events.models.EventTrigger.is_triggered", return_value=False)
    def test_process_event_trigger_device_value_has_not_changed_do_not_process(
        self, mock_is_triggered, mock_value_changed, mock_event
    ):
        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
        ]

        self.zb_msg.check_event_triggers()
        total_trigger_calls = mock_is_triggered.call_count

        self.assertEqual(total_trigger_calls, 0)

    @mock.patch("apps.mqtt.publish.send_message")
    @mock.patch("apps.events.models.EventTrigger.is_triggered", return_value=True)
    @mock.patch("apps.events.models.Event.is_enabled", return_value=True)
    @mock.patch(
        "apps.zigbee.models.ZigbeeMessage.device_value_changed", return_value=True
    )
    @mock.patch("apps.events.models.EventTriggerLog.objects.create", autospec=True)
    def test_trigger_log_created_when_a_trigger_condition_is_met(
        self, mock_log, mock_value_changed, mock_event, mock_triggered, mock_mqtt
    ):
        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=False),
        ]

        self.zb_msg.check_event_triggers()
        total_log_calls = mock_log.call_count

        self.assertEqual(total_log_calls, 1)

    @mock.patch("apps.events.models.EventTrigger.is_triggered", return_value=True)
    @mock.patch("apps.notifications.models.PushbulletNotification.send")
    @mock.patch("apps.notifications.models.EmailNotification.send")
    def test_process_event_trigger_sends_notifications_when_enabled(
        self, mock_email, mock_pushbullet, mock_triggered
    ):
        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=False),
        ]

        pb_notification = NotificationSettingFactory(
            user=self.user,
            notification_medium=NotificationMedium.PUSHBULLET,
            is_enabled=True,
        )
        pushbullet = PushbulletNotificationFactory(notification=pb_notification)
        em_notification = NotificationSettingFactory(
            user=self.user,
            notification_medium=NotificationMedium.EMAIL,
            is_enabled=True,
        )
        email = EmailNotificationFactory(notification=em_notification)

        self.zb_msg.check_event_triggers()
        total_em = mock_email.call_count
        total_pb = mock_pushbullet.call_count

        self.assertEqual(total_em, 1)
        self.assertEqual(total_pb, 1)

    @mock.patch("apps.events.models.EventTrigger.is_triggered", return_value=True)
    @mock.patch("apps.notifications.models.PushbulletNotification.send")
    def test_process_event_trigger_sends_notifications_for_each_event(
        self, mock_pushbullet, mock_triggered
    ):
        second_event = EventFactory(
            user=self.user, is_enabled=True, send_notification=True
        )

        triggers = [
            EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),
            EventTriggerFactory(
                event=second_event, device=self.device, is_enabled=True
            ),
        ]

        pb_notification = NotificationSettingFactory(
            user=self.user,
            notification_medium=NotificationMedium.PUSHBULLET,
            is_enabled=True,
        )
        pushbullet = PushbulletNotificationFactory(notification=pb_notification)

        self.zb_msg.check_event_triggers()
        total_pb = mock_pushbullet.call_count

        self.assertEqual(total_pb, 2)

    @mock.patch("apps.events.models.EventTrigger.is_triggered", return_value=True)
    @mock.patch("apps.notifications.models.PushbulletNotification.send")
    @mock.patch("apps.notifications.models.EmailNotification.send")
    def test_process_event_trigger_does_not_send_notifications_when_disabled(
        self, mock_email, mock_pushbullet, mock_triggered
    ):
        EventTriggerFactory(event=self.event, device=self.device, is_enabled=True),

        pb_notification = NotificationSettingFactory(
            user=self.user,
            notification_medium=NotificationMedium.PUSHBULLET,
            is_enabled=False,
        )
        pushbullet = PushbulletNotificationFactory(notification=pb_notification)
        em_notification = NotificationSettingFactory(
            user=self.user,
            notification_medium=NotificationMedium.EMAIL,
            is_enabled=False,
        )
        email = EmailNotificationFactory(notification=em_notification)

        self.zb_msg.check_event_triggers()

        total_em = mock_email.call_count
        total_pb = mock_pushbullet.call_count

        self.assertEqual(total_em, 0)
        self.assertEqual(total_pb, 0)

    @mock.patch("apps.events.models.EventTrigger.is_triggered", return_value=True)
    @mock.patch("apps.mqtt.publish.send_message")
    def test_invoke_event_response_successfully_sends_mqtt_messages(
        self, mock_mqtt, mock_triggered
    ):
        # add additional event responses to the one created in setUp
        EventResponseFactory(event=self.event, is_enabled=True)
        EventResponseFactory(event=self.event, is_enabled=True)

        EventTriggerFactory(event=self.event, device=self.device, is_enabled=True)

        self.zb_msg.check_event_triggers()

        total_calls = mock_mqtt.call_count

        self.assertEqual(total_calls, 3)


class TestZigbeeLog(TestCase):
    def test_string_output(self):
        log = ZigbeeLogFactory()

        self.assertEqual(str(log), f"{log.metadata_type}={log.metadata_value}")
