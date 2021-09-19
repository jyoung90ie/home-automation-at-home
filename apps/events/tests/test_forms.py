from django.test.testcases import TestCase
from django.urls import reverse

from ...devices.tests.factories import (DeviceFactory, UserFactory,
                                        ZigbeeDeviceStateFactory)
from ...zigbee.tests.factories import (ZigbeeDeviceFactory, ZigbeeLogFactory,
                                       ZigbeeMessageFactory)
from ..forms import (NON_NUMERIC_TRIGGER_TYPES, NUMERIC_TRIGGER_TYPES,
                     EventForm, EventResponseForm, EventResponseUpdateForm,
                     EventTriggerForm)
from ..models import EventTriggerType
from .factories import EventFactory, EventResponseFactory


class DummyObject:
    def __init__(self, user):
        self.user = user


class TestEventTriggerForm(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user)
        self.zb_device = ZigbeeDeviceFactory(device=self.device, is_controllable=True)
        self.event = EventFactory(user=self.user)
        self.dummy_request = DummyObject(user=self.user)
        self.zb_msg = ZigbeeMessageFactory(zigbee_device=self.zb_device)
        ZigbeeLogFactory(
            broker_message=self.zb_msg,
            metadata_type="dummy-metadata",
            metadata_value="dummy-on",
        )

        self.form_data = {
            "_device": self.device.uuid,
            "trigger_type": EventTriggerType.EQUAL,
            "_metadata_field": "dummy-metadata",
            "metadata_trigger_value": "dummy-value",
            "is_enabled": True,
        }

    def test_all_fields_appear(self):
        form = EventTriggerForm()
        self.assertIn("_device", form.fields)
        self.assertIn("is_enabled", form.fields)
        self.assertIn("_metadata_field", form.fields)
        self.assertIn("trigger_type", form.fields)
        self.assertIn("metadata_trigger_value", form.fields)

    def test_submitting_valid_data_is_accepted(self):
        devices = [
            (self.device.uuid, self.device.friendly_name),
        ]

        metadata_fields = [
            ("dummy-metadata", "dummy-metadata"),
        ]

        self.form_data["_metadata_field"] = "dummy-metadata"
        self.form_data["metadata_trigger_value"] = "dummy-on"

        form = EventTriggerForm(
            data=self.form_data,
            request=self.dummy_request,
            event_uuid=self.event.uuid,
        )
        form.fields["_device"].choices = devices
        form.fields["_metadata_field"].choices = metadata_fields

        self.assertTrue(form.is_valid())

    def test_submitting_invalid_state_for_device_throws_error(self):
        self.form_data["_metadata_field"] = "NOT A REAL FIELD"

        form = EventTriggerForm(
            data=self.form_data,
            request=self.dummy_request,
            event_uuid=self.event.uuid,
        )

        self.assertIn(
            "Select a valid choice. The value you selected is not one of the available "
            "choices.",
            form.errors["_metadata_field"],
        )
        self.assertFalse(form.is_valid())

    def test_submitting_non_numeric_value_for_numeric_trigger_type_results_in_error(
        self,
    ):
        non_numeric_value = "NOT-A-NUMBER"
        for trigger_type in NUMERIC_TRIGGER_TYPES:
            with self.subTest(trigger_type=trigger_type):
                self.form_data["trigger_type"] = trigger_type
                self.form_data["metadata_trigger_value"] = non_numeric_value

                form = EventTriggerForm(
                    data=self.form_data,
                    request=self.dummy_request,
                    event_uuid=self.event.uuid,
                )

                self.assertIn(
                    "If you wish to use a non-numeric trigger value, you can select one of the"
                    " following: EQUAL TO, NOT EQUAL TO",
                    form.errors["trigger_type"],
                )
                self.assertFalse(form.is_valid())

    def test_non_numeric_trigger_types_accept_any_value(
        self,
    ):
        non_numeric_value = "12345"
        for trigger_type in NON_NUMERIC_TRIGGER_TYPES:
            with self.subTest(trigger_type=trigger_type):
                self.form_data["trigger_type"] = trigger_type
                self.form_data["metadata_trigger_value"] = non_numeric_value

                form = EventTriggerForm(
                    data=self.form_data,
                    request=self.dummy_request,
                    event_uuid=self.event.uuid,
                )

                self.assertTrue(form.is_valid())

    def test_using_another_users_device_throws_error(
        self,
    ):
        other_user_device = DeviceFactory()
        devices = [
            (other_user_device.uuid, other_user_device.friendly_name),
        ]

        metadata_fields = [
            ("dummy-metadata", "dummy-metadata"),
        ]

        self.form_data["_metadata_field"] = "dummy-metadata"
        self.form_data["metadata_trigger_value"] = "dummy-on"
        self.form_data["_device"] = other_user_device.uuid

        form = EventTriggerForm(
            data=self.form_data,
            request=self.dummy_request,
            event_uuid=self.event.uuid,
        )
        form.fields["_device"].choices = devices
        form.fields["_metadata_field"].choices = metadata_fields

        self.assertIn(
            "Select a valid choice. The value you selected is not one of the available choices.",
            form.errors["_device"],
        )
        self.assertFalse(form.is_valid())

    def test_fields_are_saved_as_expected(self):
        devices = [
            (self.device.uuid, self.device.friendly_name),
        ]

        metadata_fields = [
            ("dummy-metadata", "dummy-metadata"),
        ]

        self.form_data["_metadata_field"] = "dummy-metadata"
        self.form_data["metadata_trigger_value"] = "dummy-on"
        self.form_data["_device"] = self.device.uuid

        form = EventTriggerForm(
            data=self.form_data,
            request=self.dummy_request,
            event_uuid=self.event.uuid,
        )
        form.fields["_device"].choices = devices
        form.fields["_metadata_field"].choices = metadata_fields

        # save form
        if form.is_valid():
            obj = form.save()
            # device should not have changed
            self.assertEqual(obj.event, self.event)
            self.assertEqual(obj.device, self.device)
            self.assertEqual(obj.metadata_field, "dummy-metadata")
            self.assertEqual(obj.metadata_trigger_value, "dummy-on")
            self.assertEqual(obj.trigger_type, self.form_data["trigger_type"])
            self.assertEqual(obj.is_enabled, self.form_data["is_enabled"])
        else:
            self.fail("Form is not valid")


class TestEventResponseForm(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user)
        self.zb_device = ZigbeeDeviceFactory(device=self.device, is_controllable=True)
        self.state = ZigbeeDeviceStateFactory(content_object=self.zb_device)
        self.dummy_request = DummyObject(user=self.user)
        self.event = EventFactory(user=self.user)

        self.form_data = {
            "_device": self.device.uuid,
            "_state": self.state.uuid,
            "is_enabled": True,
        }

    def test_all_fields_appear(self):
        form = EventResponseForm()
        self.assertIn("_device", form.fields)
        self.assertIn("_state", form.fields)
        self.assertIn("is_enabled", form.fields)

    def test_submitting_valid_data_is_accepted(self):
        devices = [
            (self.device.uuid, self.device.friendly_name),
        ]

        states = [(self.state.uuid, self.state.name)]

        form = EventResponseForm(
            data=self.form_data,
            request=self.dummy_request,
            event_uuid=self.event.uuid,
        )
        form.fields["_device"].choices = devices
        form.fields["_state"].choices = states

        self.assertTrue(form.is_valid())

    def test_using_a_device_that_is_not_controllable_throws_an_error(self):
        not_controllable_device = DeviceFactory(user=self.user)
        ZigbeeDeviceFactory(device=not_controllable_device, is_controllable=False)

        devices = [
            (self.device.uuid, self.device.friendly_name),
            (not_controllable_device.uuid, not_controllable_device.friendly_name),
        ]

        states = [(self.state.uuid, self.state.name)]

        self.form_data["_device"] = not_controllable_device.uuid

        form = EventResponseForm(
            data=self.form_data,
            request=self.dummy_request,
            event_uuid=self.event.uuid,
        )
        form.fields["_device"].choices = devices
        form.fields["_state"].choices = states

        self.assertIn(
            "Select a valid choice. The value you selected is not one of the available"
            " choices.",
            form.errors["_device"],
        )
        self.assertFalse(form.is_valid())

    def test_using_a_device_that_is_not_linked_throws_an_error(self):
        not_linked_device = DeviceFactory(user=self.user)

        devices = [
            (self.device.uuid, self.device.friendly_name),
            (not_linked_device.uuid, not_linked_device.friendly_name),
        ]

        states = [(self.state.uuid, self.state.name)]

        self.form_data["_device"] = not_linked_device.uuid

        form = EventResponseForm(
            data=self.form_data,
            request=self.dummy_request,
            event_uuid=self.event.uuid,
        )
        form.fields["_device"].choices = devices
        form.fields["_state"].choices = states

        self.assertIn(
            "Select a valid choice. The value you selected is not one of the available"
            " choices.",
            form.errors["_device"],
        )
        self.assertFalse(form.is_valid())

    def test_using_another_users_device_throws_an_error(
        self,
    ):
        other_device = DeviceFactory()
        other_zb_device = ZigbeeDeviceFactory(
            device=other_device, is_controllable=False
        )

        devices = [
            (self.device.uuid, self.device.friendly_name),
            (other_device.uuid, other_device.friendly_name),
        ]

        states = [
            (self.state.uuid, self.state.name),
        ]

        self.form_data["_device"] = other_device.uuid

        form = EventResponseForm(
            data=self.form_data,
            request=self.dummy_request,
            event_uuid=self.event.uuid,
        )
        form.fields["_device"].choices = devices
        form.fields["_state"].choices = states

        self.assertIn(
            "Select a valid choice. The value you selected is not one of the available"
            " choices.",
            form.errors["_device"],
        )
        self.assertFalse(form.is_valid())

    def test_selecting_valid_device_with_state_for_another_device_results_in_error(
        self,
    ):
        other_device = DeviceFactory()
        other_zb_device = ZigbeeDeviceFactory(
            device=other_device, is_controllable=False
        )
        other_device_state = ZigbeeDeviceStateFactory(content_object=other_zb_device)

        devices = [
            (self.device.uuid, self.device.friendly_name),
        ]

        states = [
            (self.state.uuid, self.state.name),
            (other_device_state.uuid, other_device_state.name),
        ]

        self.form_data["_device"] = self.device.uuid
        self.form_data["_state"] = other_device_state.uuid

        form = EventResponseForm(
            data=self.form_data,
            request=self.dummy_request,
            event_uuid=self.event.uuid,
        )
        form.fields["_device"].choices = devices
        form.fields["_state"].choices = states

        self.assertIn(
            "Select a valid choice. The value you selected is not one of the available"
            " choices.",
            form.errors["_state"],
        )
        self.assertFalse(form.is_valid())


class TestEventResponseUpdateForm(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.device = DeviceFactory(user=self.user)
        self.zb_device = ZigbeeDeviceFactory(device=self.device, is_controllable=True)
        self.state = ZigbeeDeviceStateFactory(content_object=self.zb_device)
        self.event = EventFactory(user=self.user)
        self.event_response = EventResponseFactory(
            event=self.event, device_state=self.state, is_enabled=False
        )
        self.dummy_request = DummyObject(user=self.user)

    def test_all_fields_appear(self):
        form = EventResponseUpdateForm()
        self.assertIn("_device", form.fields)
        self.assertIn("_state", form.fields)
        self.assertIn("is_enabled", form.fields)

    def test_device_field_is_readonly(self):
        form = EventResponseUpdateForm()

        self.assertTrue(form.fields["_device"].disabled)

    def test_device_is_passed_through(self):
        form_data = {
            "_device": "",
            "_state": self.state.uuid,
            "is_enabled": True,
        }

        devices = [
            (self.device.uuid, self.device.friendly_name),
        ]

        states = [
            (self.state.uuid, self.state.name),
        ]

        # check initial value
        self.assertFalse(self.event_response.is_enabled)

        form = EventResponseUpdateForm(
            data=form_data,
            instance=self.event_response,  # initialise
            device=self.device,
            event_uuid=self.event.uuid,
        )

        form.fields["_device"].choices = devices
        form.fields["_state"].choices = states

        # save form
        if form.is_valid():
            obj = form.save()

            self.assertEqual(obj.device_state.content_object.device, self.device)
            # check object was updated with new value
            self.assertTrue(self.event_response.is_enabled)
        else:
            self.fail("Form is not valid")

    def test_updating_device_does_not_change_device_but_other_values_updated(self):
        other_device = DeviceFactory()

        form_data = {
            "_device": other_device,
            "_state": self.state.uuid,
            "is_enabled": True,
        }

        devices = [
            (self.device.uuid, self.device.friendly_name),
            (other_device.uuid, other_device.friendly_name),
        ]

        states = [
            (self.state.uuid, self.state.name),
        ]

        # check initial values
        self.assertEqual(
            self.event_response.device_state.content_object.device, self.device
        )
        self.assertFalse(self.event_response.is_enabled)
        self.assertFalse(other_device.user == self.user)

        form = EventResponseUpdateForm(
            data=form_data,
            instance=self.event_response,  # initialise
            device=self.device,
            event_uuid=self.event.uuid,
        )

        form.fields["_device"].choices = devices
        form.fields["_state"].choices = states

        # save form
        if form.is_valid():
            obj = form.save()
            # device should not have changed
            self.assertEqual(obj.device_state.content_object.device, self.device)
            # check object was updated with new value
            self.assertTrue(self.event_response.is_enabled)
        else:
            self.fail("Form is not valid")


class TestEventForm(TestCase):
    def test_all_fields_appear(self):
        form = EventForm()
        self.assertIn("description", form.fields)
        self.assertIn("is_enabled", form.fields)
        self.assertIn("send_notification", form.fields)
        self.assertIn("notification_topic", form.fields)
        self.assertIn("notification_message", form.fields)
