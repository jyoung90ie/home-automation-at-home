from typing import Tuple

from django.db.models.query import QuerySet
from django.test.testcases import TestCase

from ...devices.models import DeviceProtocol
from ...zigbee.models import ZigbeeDevice, ZigbeeLog
from ...zigbee.tests.factories import (
    ZigbeeDeviceFactory,
    ZigbeeLogFactory,
    ZigbeeMessageFactory,
)
from .factories import (
    DeviceFactory,
    DeviceLocationFactory,
    UserFactory,
    ZigbeeDeviceStateFactory,
)

from ...events.tests.factories import EventTriggerFactory


class DeviceTestMixin(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user, protocol=DeviceProtocol.ZIGBEE)

    def generate_logs(
        self,
        total_messages: int = 3,
        total_logs: int = 10,
    ) -> Tuple["ZigbeeMessageFactory", "ZigbeeLogFactory"]:
        msgs = []
        logs = []

        zb_device = ZigbeeDeviceFactory(device=self.device)

        for _ in range(total_messages):
            msgs.append(ZigbeeMessageFactory(zigbee_device=zb_device))

        for num in range(total_logs):
            zb_msg = msgs[num % total_messages]
            logs.append(ZigbeeLogFactory(broker_message=zb_msg))

        return msgs, logs


class TestDeviceLinkDevice(DeviceTestMixin):
    def link_device(self):
        self.zb_device = ZigbeeDeviceFactory()
        self.device.device_identifier = self.zb_device.ieee_address
        self.device.save()
        self.assertTrue(self.device.is_linked())

    def test_saving_model_converts_to_lowercase(self):
        self.device.friendly_name = "TEST1234"
        self.device.device_identifier = "TEST1234"
        self.device.save()

        self.assertEqual(self.device.friendly_name, "test1234")
        self.assertEqual(self.device.device_identifier, "test1234")

    def test_that_zigbee_device_is_linked_on_save_when_friendly_name_matches(self):
        zb_device = ZigbeeDeviceFactory(friendly_name="Test-Device-123")

        self.assertFalse(self.device.is_linked())

        self.device.friendly_name = "Test-Device-123"
        self.device.save()

        self.assertTrue(self.device.is_linked())
        self.assertEqual(self.device.get_linked_device(), zb_device)

    def test_that_zigbee_device_is_linked_on_save_when_device_identifier_matches(self):
        zb_device = ZigbeeDeviceFactory(ieee_address="TEST-1234567890")

        self.assertFalse(self.device.is_linked())

        self.device.device_identifier = "TEST-1234567890"
        self.device.save()

        self.assertTrue(self.device.is_linked())
        self.assertEqual(self.device.get_linked_device(), zb_device)

    def test_zigbee_model_is_attached(self):
        self.assertTrue(self.device.zigbee_model is not None)

    def test_get_zigbee_device_when_not_linked_returns_none(self):
        self.assertFalse(self.device.is_linked())
        self.assertTrue(self.device.get_zigbee_device() is None)

    def test_get_zigbee_device_when_linked_return_device(self):
        self.link_device()
        self.assertTrue(isinstance(self.device.get_zigbee_device(), ZigbeeDevice))
        self.assertEqual(self.zb_device, self.device.get_zigbee_device())


class TestDeviceGetZigbeeMessages(DeviceTestMixin):
    def test_returns_none_when_device_not_linked(self):
        msgs = self.device.get_zigbee_messages()

        self.assertTrue(msgs is None)

    def test_returns_empty_queryset(self):
        ZigbeeDeviceFactory(device=self.device)

        msgs = self.device.get_zigbee_messages()

        self.assertTrue(isinstance(msgs, QuerySet))
        self.assertEqual(len(msgs), 0)

    def test_returns_all_expected_messages(self):
        zb_device = ZigbeeDeviceFactory(device=self.device)

        self.assertEqual(len(self.device.get_zigbee_messages()), 0)

        zb_message1 = ZigbeeMessageFactory(zigbee_device=zb_device)
        zb_message2 = ZigbeeMessageFactory(zigbee_device=zb_device)
        zb_message3 = ZigbeeMessageFactory(zigbee_device=zb_device)

        zb_msgs = [zb_message1, zb_message2, zb_message3]

        device_msgs = self.device.get_zigbee_messages()

        self.assertEqual(len(device_msgs), 3)

        for zb_msg in zb_msgs:
            with self.subTest(zigbee_message=zb_msg):
                self.assertTrue(zb_msg in device_msgs)

    def test_does_not_return_other_device_message(self):
        zb_device = ZigbeeDeviceFactory(device=self.device)
        ZigbeeMessageFactory(zigbee_device=zb_device)
        ZigbeeMessageFactory(zigbee_device=zb_device)
        ZigbeeMessageFactory(zigbee_device=zb_device)

        other_zb_device = ZigbeeDeviceFactory()

        self.assertEqual(len(other_zb_device.device.get_zigbee_messages()), 0)


class TestDeviceGetZigbeeLogs(DeviceTestMixin):
    def test_returns_none_when_device_not_linked(self):
        logs = self.device.get_zigbee_logs()

        self.assertTrue(logs is None)

    def test_returns_none_when_there_are_no_zigbee_messages(self):
        ZigbeeDeviceFactory(device=self.device)

        logs = self.device.get_zigbee_logs()

        self.assertTrue(self.device.is_linked())
        self.assertTrue(logs is None)

    def test_passing_no_parameters_returns_all_device_logs(self):
        msgs, logs = self.generate_logs()

        device_logs = self.device.get_zigbee_logs()

        self.assertEqual(len(logs), len(device_logs))

        for device_log in device_logs:
            with self.subTest(device_log=device_log):
                self.assertTrue(device_log in logs)

    def test_passing_latest_only_returns_the_latest(self):
        msgs, logs = self.generate_logs()

        device_logs = self.device.get_zigbee_logs(latest_only=True)

        last_msg = msgs[-1]

        last_msg_logs = ZigbeeLog.objects.filter(broker_message=last_msg)
        total_logs_for_last_msg = last_msg_logs.count()

        self.assertEqual(len(device_logs), total_logs_for_last_msg)

        for device_log in device_logs:
            with self.subTest(device_log=device_log):
                self.assertTrue(device_log in last_msg_logs)

    def test_passing_message_object_returns_only_logs_for_that_object(self):
        msgs, logs = self.generate_logs()

        print("msgs=", msgs)

        logs_for_message = msgs[0]
        print("logs_for_message_test=", logs_for_message)

        device_logs = self.device.get_zigbee_logs(filter_message=logs_for_message)

        last_msg_logs = ZigbeeLog.objects.filter(broker_message=logs_for_message)
        total_logs_for_last_msg = last_msg_logs.count()

        self.assertEqual(len(device_logs), total_logs_for_last_msg)

        for device_log in device_logs:
            with self.subTest(device_log=device_log):
                self.assertTrue(device_log in last_msg_logs)


class TestDeviceGetLatestZigbeeLogs(DeviceTestMixin):
    def test_returns_none_when_device_not_linked(self):
        logs = self.device.get_latest_zigbee_logs()

        self.assertTrue(logs is None)

    def test_returns_none_when_there_are_no_zigbee_messages(self):
        ZigbeeDeviceFactory(device=self.device)

        logs = self.device.get_latest_zigbee_logs()

        self.assertTrue(self.device.is_linked())
        self.assertTrue(logs is None)

    def test_passing_latest_only_returns_the_latest(self):
        msgs, logs = self.generate_logs()

        device_logs = self.device.get_latest_zigbee_logs()

        last_msg = msgs[-1]

        last_msg_logs = ZigbeeLog.objects.filter(broker_message=last_msg)
        total_logs_for_last_msg = last_msg_logs.count()

        self.assertEqual(len(device_logs), total_logs_for_last_msg)

        for device_log in device_logs:
            with self.subTest(device_log=device_log):
                self.assertTrue(device_log in last_msg_logs)


class TestDeviceTryToLinkZigbeeDevice(DeviceTestMixin):
    def test_that_api_device_is_not_linked(self):
        device = DeviceFactory(user=self.user, protocol=DeviceProtocol.API)

        ZigbeeDeviceFactory(
            ieee_address=device.device_identifier, friendly_name=device.friendly_name
        )  # using zigbeedevice as no other device exists yet

        device.try_to_link_zigbee_device()

        self.assertTrue(device.protocol, DeviceProtocol.API)
        self.assertFalse(device.is_linked())

    def test_that_zigbee_device_is_linked_when_device_matches_identifier(self):
        ZigbeeDeviceFactory(ieee_address=self.device.device_identifier)

        self.device.try_to_link_zigbee_device()

        self.assertTrue(self.device.protocol, DeviceProtocol.ZIGBEE)
        self.assertTrue(self.device.is_linked())

    def test_that_zigbee_device_is_linked_when_device_matches_friendly_name(self):
        ZigbeeDeviceFactory(friendly_name=self.device.friendly_name)

        self.device.try_to_link_zigbee_device()

        self.assertTrue(self.device.protocol, DeviceProtocol.ZIGBEE)
        self.assertTrue(self.device.is_linked())

    def test_that_device_is_not_linked_when_details_do_not_match(self):
        device = DeviceFactory(user=self.user, protocol=DeviceProtocol.ZIGBEE)

        ZigbeeDeviceFactory()

        device.try_to_link_zigbee_device()

        self.assertTrue(device.protocol, DeviceProtocol.ZIGBEE)
        self.assertFalse(device.is_linked())


class TestDeviceGetLinkedDevice(DeviceTestMixin):
    def test_that_nothing_is_returned_when_device_is_not_linked(self):
        self.assertTrue(self.device is not None)
        self.assertTrue(self.device.get_linked_device() is None)

    def test_that_linked_device_is_returned(self):
        zb_device = ZigbeeDeviceFactory(device=self.device)

        linked_device = self.device.get_linked_device()

        self.assertTrue(linked_device == zb_device)
        self.assertTrue(isinstance(linked_device, ZigbeeDevice))

    def test_that_only_first_device_is_returned_if_multiple_devices_mistakenly_linked(
        self,
    ):
        zb_device1 = ZigbeeDeviceFactory(device=self.device)
        zb_device2 = ZigbeeDeviceFactory(device=self.device)
        zb_device3 = ZigbeeDeviceFactory(device=self.device)

        linked_device = self.device.get_linked_device()

        self.assertTrue(linked_device == zb_device1)
        self.assertTrue(isinstance(linked_device, ZigbeeDevice))


class TestDeviceGetLinkedDeviceValues(DeviceTestMixin):
    def test_that_nothing_is_returned_when_device_is_not_linked(self):
        self.assertTrue(self.device is not None)
        self.assertTrue(self.device.get_linked_device() is None)

    def test_that_linked_device_values_are_returned(self):
        zb_device = ZigbeeDeviceFactory(device=self.device)

        linked_device_values = self.device.get_linked_device_values()

        zb_device_values = ZigbeeDevice.objects.values().last()

        self.assertTrue(isinstance(linked_device_values, dict))
        self.assertTrue(linked_device_values == zb_device_values)


class TestDeviceIsLinked(DeviceTestMixin):
    def test_when_linked_returns_true(self):
        zb_device = ZigbeeDeviceFactory(device=self.device)

        self.assertTrue(self.device.is_linked())

    def test_when_not_linked_returns_false(self):
        self.assertFalse(self.device.is_linked())


class TestDeviceIsControllable(DeviceTestMixin):
    def test_when_device_is_not_linked_returns_false(self):
        self.assertFalse(self.device.is_linked())
        self.assertFalse(self.device.is_controllable())

    def test_when_device_is_linked_but_not_controllable_returns_false(self):
        zb_device = ZigbeeDeviceFactory(device=self.device, is_controllable=False)
        self.assertTrue(self.device.is_linked())
        self.assertFalse(self.device.is_controllable())

    def test_when_device_is_linked_and_controllable_returns_true(self):
        zb_device = ZigbeeDeviceFactory(device=self.device, is_controllable=True)
        self.assertTrue(self.device.is_linked())
        self.assertTrue(self.device.is_controllable())


class TestDeviceGetEventTriggers(DeviceTestMixin):
    def test_when_device_has_no_eventtriggers_returns_empty_queryset(self):
        # zb_device = ZigbeeDeviceFactory(device=self.device)

        event_triggers = self.device.get_event_triggers()

        self.assertTrue(len(event_triggers) == 0)
        self.assertTrue(isinstance(event_triggers, QuerySet))

    def test_returns_only_enabled_event_triggers(self):
        triggers = [
            EventTriggerFactory(device=self.device, is_enabled=True),
            EventTriggerFactory(device=self.device, is_enabled=False),
            EventTriggerFactory(device=self.device, is_enabled=True),
        ]

        event_triggers = self.device.get_event_triggers()

        self.assertTrue(len(event_triggers) == 2)

        for trigger in triggers:
            with self.subTest(trigger=trigger):
                if trigger.is_enabled:
                    self.assertTrue(trigger in event_triggers)
                else:
                    self.assertFalse(trigger in event_triggers)

    def test_does_not_return_triggers_for_other_devices(self):
        triggers = [
            EventTriggerFactory(device=self.device, is_enabled=True),
            EventTriggerFactory(is_enabled=True),
            EventTriggerFactory(is_enabled=True),
        ]

        event_triggers = self.device.get_event_triggers()

        self.assertTrue(len(event_triggers) == 1)

        for trigger in triggers:
            with self.subTest(trigger=trigger):
                if trigger.device == self.device:
                    self.assertTrue(trigger in event_triggers)
                else:
                    self.assertFalse(trigger in event_triggers)


class TestDeviceLocation(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.location = DeviceLocationFactory(
            user=self.user,
        )

    def test_location_name_is_saved_as_lower_case(self):
        self.location.location = "THIS IS IN UPPERCASE"
        self.location.save()

        self.assertNotEqual(self.location.location, "THIS IS IN UPPERCASE")
        self.assertEqual(self.location.location, "this is in uppercase")

    def test_get_linked_devices_only_returns_devices_with_same_location(self):
        devices = [
            DeviceFactory(
                user=self.user, location=self.location, protocol=DeviceProtocol.ZIGBEE
            ),
            DeviceFactory(
                user=self.user, location=self.location, protocol=DeviceProtocol.ZIGBEE
            ),
            DeviceFactory(user=self.user, protocol=DeviceProtocol.ZIGBEE),
        ]

        zb_devices = [
            ZigbeeDeviceFactory(device=devices[0]),
            ZigbeeDeviceFactory(device=devices[1]),
            ZigbeeDeviceFactory(device=devices[2]),
        ]

        linked_devices = self.location.get_linked_devices()

        self.assertEqual(len(linked_devices), 2)
        self.assertEqual(self.location.total_linked_devices(), 2)

        for zb_device in zb_devices:
            with self.subTest(zb_device=zb_device):
                if zb_device.device.location == self.location:
                    self.assertTrue(zb_device.device in linked_devices)
                else:
                    self.assertFalse(zb_device.device in linked_devices)

    def test_total_linked_devices_is_zero_when_no_devices(self):
        self.assertEqual(self.location.total_linked_devices(), 0)


class TestDeviceState(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user)
        self.state = ZigbeeDeviceStateFactory(content_object=self.device)
