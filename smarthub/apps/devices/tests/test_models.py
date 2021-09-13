from typing import Tuple

from django.db.models.query import QuerySet
from django.test.testcases import TestCase

from ...devices.models import DeviceProtocol
from ...zigbee.models import ZigbeeDevice, ZigbeeLog
from ...zigbee.tests.factories import (ZigbeeDeviceFactory, ZigbeeLogFactory,
                                       ZigbeeMessageFactory)
from .factories import (DeviceFactory, DeviceLocationFactory, UserFactory,
                        ZigbeeDeviceStateFactory)


class DeviceMixinForTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user)

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


class TestDeviceLinkDevice(DeviceMixinForTest):
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


class TestDeviceGetZigbeeMessages(DeviceMixinForTest):
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


class TestDeviceGetZigbeeLogs(DeviceMixinForTest):
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


class TestDeviceGetLatestZigbeeLogs(DeviceMixinForTest):
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


class TestDeviceTryToLinkZigbeeDevice(DeviceMixinForTest):
    def test_that_api_device_is_not_linked(self):
        device = DeviceFactory(user=self.user, protocol=DeviceProtocol.API)

        ZigbeeDeviceFactory(
            ieee_address=device.device_identifier, friendly_name=device.friendly_name
        )  # using zigbeedevice as no other device exists yet

        device.try_to_link_zigbee_device()

        self.assertTrue(device.protocol, DeviceProtocol.API)
        self.assertFalse(device.is_linked())

    def test_that_zigbee_device_is_linked(self):
        device = DeviceFactory(user=self.user, protocol=DeviceProtocol.ZIGBEE)

        ZigbeeDeviceFactory(
            ieee_address=device.device_identifier, friendly_name=device.friendly_name
        )

        device.try_to_link_zigbee_device()

        self.assertTrue(device.protocol, DeviceProtocol.ZIGBEE)
        self.assertTrue(device.is_linked())


class TestDeviceLocation(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.location = DeviceLocationFactory(
            user=self.user,
        )


class TestDeviceState(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user)
        self.state = ZigbeeDeviceStateFactory(content_object=self.device)
