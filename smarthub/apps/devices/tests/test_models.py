from ...zigbee.models import ZigbeeDevice
from django.test.testcases import TestCase
import factory
from .factories import (
    DeviceFactory,
    DeviceLocationFactory,
    UserFactory,
    ZigbeeDeviceStateFactory,
)
from ...zigbee.tests.factories import (
    ZigbeeDeviceFactory,
    ZigbeeLogFactory,
    ZigbeeMessageFactory,
)


class TestDeviceLocation(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.location = DeviceLocationFactory(
            user=self.user,
        )


class TestDevice(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user)

    def link_device(self):
        zb_device = ZigbeeDeviceFactory()
        self.device.device_identifier = zb_device.ieee_address
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
        self.assertEqual(self.device.get_linked_device().first(), zb_device)

    def test_that_zigbee_device_is_linked_on_save_when_device_identifier_matches(self):
        zb_device = ZigbeeDeviceFactory(ieee_address="TEST-1234567890")

        self.assertFalse(self.device.is_linked())

        self.device.device_identifier = "TEST-1234567890"
        self.device.save()

        self.assertTrue(self.device.is_linked())
        self.assertEqual(self.device.get_linked_device().first(), zb_device)

    def test_zigbee_model_is_attached(self):
        self.assertTrue(self.device.zigbee_model is not None)

    def test_get_zigbee_device_when_not_linked_returns_none(self):
        self.assertFalse(self.device.is_linked())
        self.assertTrue(self.device.get_zigbee_device() is None)

    def test_get_zigbee_device_when_linked_return_device(self):
        self.link_device()
        self.assertTrue(
            isinstance(self.device.get_zigbee_device().first(), ZigbeeDevice)
        )


class TestDeviceState(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user)
        self.state = ZigbeeDeviceStateFactory(content_object=self.device)
