from django.test import TestCase
from django.urls import reverse

from .factories import DeviceFactory, DeviceLocationFactory, UserFactory
from .helpers import (
    assert_object_values_in_response,
    assert_values_in_reponse,
    create_objects,
)

login_url = reverse("account_login")


class TestListDevices(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

        self.url = reverse("devices:list")

    def test_anonymous_user_cannot_access_view_pass(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_when_no_devices_exist_message_is_shown(self):
        response = self.client.get(self.url)

        values = [
            {
                "value": "you do not have any devices",
                "exists": True,
            },
        ]

        self.assertEqual(response.status_code, 200)
        assert_values_in_reponse(response=response, values=values)

    def test_user_devices_listed(self):
        devices = create_objects(user=self.user, object_factory=DeviceFactory)
        response = self.client.get(self.url)

        assert_object_values_in_response(
            response=response,
            objects=devices,
            field="friendly_name",
            exists=True,
        )

    def test_user_cannot_see_other_user_devices(self):
        other_user = UserFactory()
        other_user_devices = create_objects(
            user=other_user, object_factory=DeviceFactory
        )
        response = self.client.get(self.url)

        values = [
            {"value": "you do not have any devices", "exists": True},
        ]
        assert_values_in_reponse(response=response, values=values)

        assert_object_values_in_response(
            response=response,
            objects=other_user_devices,
            field="friendly_name",
            exists=False,
        )

        # change user and check that devices exist
        self.client.logout()
        self.client.force_login(user=other_user)

        response = self.client.get(self.url)

        values = [
            {"value": "you do not have any devices", "exists": False},
        ]
        assert_values_in_reponse(response=response, values=values)

        assert_object_values_in_response(
            response=response,
            objects=other_user_devices,
            field="friendly_name",
            exists=True,
        )


class TestDetailDevice(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(user=self.user)

    def get_url_response(self, uuid=None, url=None):
        if not url:
            url = reverse("devices:device:detail", kwargs={"uuid": uuid})

        return self.client.get(url)

    def test_invalid_uuid(self):
        invalid_uuid = "this-is-an-invalid-uuid"
        url = f"/devices/{invalid_uuid}/"

        response = self.get_url_response(url=url)

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()
        other_user_device = DeviceFactory(user=self.user)

        response = self.get_url_response(uuid=other_user_device.uuid)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_cannot_access_another_users_device(self):
        other_user_device = DeviceFactory()

        response = self.get_url_response(uuid=other_user_device.uuid)

        self.assertTrue(other_user_device.user != self.user)
        self.assertEqual(response.status_code, 403)

    def test_device_attributes_listed(self):
        device = DeviceFactory(user=self.user)

        response = self.get_url_response(uuid=device.uuid)

        device_detail = f"""<div class="row content-box">
        <div class="fw-bold col-4 col-md-2">Friendly Name</div>
        <div class="col-8 col-md-4">{device.friendly_name}</div>
        <div class="fw-bold col-4 col-md-2">Device Identifier</div>
        <div class="col-8 col-md-4">{device.device_identifier}</div>
        <div class="fw-bold col-4 col-md-2">Location</div>
        <div class="col-8 col-md-4">{device.location.location}</div>
        <div class="fw-bold col-4 col-md-2">Protocol</div>
        <div class="col-8 col-md-4">{device.protocol}</div>
    </div>"""

        values = [
            {
                "value": device_detail,
                "exists": True,
            },
        ]
        self.assertEqual(response.status_code, 200)
        assert_values_in_reponse(response=response, values=values)

    def test_device_is_not_linked_and_no_state_by_default(self):
        device = DeviceFactory(user=self.user)

        response = self.get_url_response(uuid=device.uuid)

        values = [
            {
                "value": "Your device has not yet been linked to a hardware device.",
                "exists": True,
            },
            {
                "value": "This device does not yet have any states - you can add some using the button above.",
                "exists": True,
            },
        ]

        self.assertEqual(response.status_code, 200)
        assert_values_in_reponse(response=response, values=values)

    def test_detail_shows_linked_device(self):
        pass


class TestAddDevice(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

        self.url = reverse("devices:add")

        return super().setUp()

    def test_anonymous_user_cannot_access_view_pass(self):
        self.client.logout()  # user is logged in as part of setup - need to logout before testing
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_create_device_form_does_not_show_when_no_device_locations_added(self):
        response = self.client.get(self.url)

        values = [
            {
                "value": "You must add at least one device location before you can add a device",
                "exists": True,
            },
            {"value": '<form method="post">', "exists": False},
        ]
        assert_values_in_reponse(response=response, values=values)

    def test_that_user_can_create_a_device_when_they_have_device_locations(self):
        # device_location = DeviceLocationFactory(user=self.user)
        device_locations = create_objects(
            user=self.user, object_factory=DeviceLocationFactory
        )
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        assert_object_values_in_response(
            response=response,
            objects=device_locations,
            field="location",
            exists=True,
        )

        values = [
            {
                "value": "You must add at least one device location before you can add a device",
                "exists": False,
            },
        ]
        assert_values_in_reponse(response=response, values=values)

    def test_other_user_locations_not_shown_to_current_user_in_create_device(self):
        current_user_device_locations = create_objects(
            user=self.user, object_factory=DeviceLocationFactory
        )

        other_user = UserFactory()
        other_user_device_locations = create_objects(
            user=other_user, object_factory=DeviceLocationFactory
        )

        response = self.client.get(self.url)

        assert_object_values_in_response(
            response=response,
            objects=current_user_device_locations,
            field="location",
            exists=True,
        )
        assert_object_values_in_response(
            response=response,
            objects=other_user_device_locations,
            field="location",
            exists=False,
        )


class TestUpdateDevice(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

        self.device = DeviceFactory(
            user=self.user,
            friendly_name="Test Device",
            device_identifier="TEST1234",
        )
        self.url = reverse("devices:device:update", kwargs={"uuid": self.device.uuid})

    def test_that_update_view_populates_device_details(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        values = [
            {
                "value": self.device.friendly_name,
                "exists": True,
            },
            {
                "value": self.device.device_identifier,
                "exists": True,
            },
            {
                "value": self.device.location.location,
                "exists": True,
            },
        ]
        assert_values_in_reponse(response=response, values=values)

    def test_that_current_user_cannot_view_update_form_for_another_users_device(self):
        other_user_device = DeviceFactory()

        url = reverse("devices:device:update", kwargs={"uuid": other_user_device.uuid})
        response = self.client.get(url)

        self.assertFalse(other_user_device.user == self.user)
        self.assertEqual(response.status_code, 403)

    def test_update_device_with_invalid_uuid_pass(self):
        def get_url_response(uuid):
            url = f"/devices/{uuid}/update/"
            return self.client.get(url)

        # make sure valid uuid returns 200 before testing - ensuring hardcoded URL is valid
        valid_uuid = self.device.uuid
        response = get_url_response(valid_uuid)
        self.assertEqual(response.status_code, 200)

        # repeat for invalid
        invalid_uuid = "this-is-an-invalid-uuid"
        response = get_url_response(invalid_uuid)
        self.assertEqual(response.status_code, 404)

    def test_view_updates_own_device_pass(self):
        new_location = DeviceLocationFactory(user=self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        updated_data = {
            "friendly_name": "NewFriendlyName",
            "device_identifier": self.device.device_identifier,
            "location": new_location.id,
            "protocol": self.device.protocol,
        }
        response = self.client.post(self.url, updated_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("devices:device:detail", kwargs={"uuid": self.device.uuid}),
        )

    def test_that_another_user_cannot_update_current_users_device(self):
        other_user_device = DeviceFactory()
        updated_data = {
            "friendly_name": "NewFriendlyName",
            "device_identifier": self.device.device_identifier,
            "location": self.device.location,
            "protocol": self.device.protocol,
        }
        response = self.client.post(
            reverse("devices:device:update", kwargs={"uuid": other_user_device.uuid}),
            updated_data,
            follow=True,
        )
        self.assertFalse(other_user_device.user == self.user)
        self.assertEqual(response.status_code, 403)

    def test_that_anonymous_users_are_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))


class TestDeleteDevice(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

        self.device = DeviceFactory(
            user=self.user,
            friendly_name="Test Device",
            device_identifier="TEST1234",
        )
        self.url = reverse("devices:device:delete", kwargs={"uuid": self.device.uuid})

    def test_delete_own_device_pass(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        values = [
            {
                "value": '<input type="submit" class="btn btn-danger" value="Delete">',
                "exists": True,
            },
        ]
        assert_values_in_reponse(response=response, values=values)

    def test_delete_other_users_device_fail(self):
        other_user_device = DeviceFactory()
        url = reverse("devices:device:delete", kwargs={"uuid": other_user_device.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_is_redirected_to_login_page(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_delete_view_deletes_device(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("devices:list"))

        # check if device page exists
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class TestDeviceMetadata(TestCase):
    def test_no_results_when_device_is_not_linked(self):
        pass

    def test_cannot_view_other_users_device_metadata(self):
        pass

    def test_nothing_displayed_when_device_is_linked_but_has_no_data(self):
        pass

    def test_only_unique_metadata_is_returned(self):
        pass

    def test_anonymous_users_are_redirected_to_login(self):
        pass


class TestDeviceStatesJson(TestCase):
    def test_cannot_view_other_users_device_state(self):
        pass

    def test_that_user_cannot_create_state_without_a_device(self):
        pass

    def test_that_all_device_states_listed_under_device(self):
        pass

    def test_that_user_can_edit_device_state(self):
        pass

    def test_that_user_can_delete_device_state(self):
        pass


class TestLogsForDevice(TestCase):
    pass


class TestExportCSVDeviceLogs(TestCase):
    pass


class TestDeviceRedirectView(TestCase):
    pass


class TestAddDeviceState(TestCase):
    pass


class TestDeleteDeviceState(TestCase):
    pass


class TestUpdateDeviceState(TestCase):
    pass


class TestListDeviceLocations(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

        self.url = reverse("devices:locations:list")

    def test_user_is_shown_message_when_no_locations(self):
        response = self.client.get(self.url)

        values = [
            {
                "value": "you have not added any locations",
                "exists": True,
            },
            {
                "value": '<table class="table table-hover">',
                "exists": False,
            },
        ]

        self.assertEqual(response.status_code, 200)
        assert_values_in_reponse(response=response, values=values)

    def test_anonymous_users_are_redirected_to_login_page(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_location_appears_in_list_when_added(self):
        device_locations = create_objects(
            user=self.user, object_factory=DeviceLocationFactory
        )

        response = self.client.get(self.url)

        assert_object_values_in_response(
            response=response, objects=device_locations, field="location"
        )

    def test_that_another_users_locations_do_not_appear(self):
        current_user_device_locations = create_objects(
            user=self.user, object_factory=DeviceLocationFactory
        )
        other_user = UserFactory()
        other_user_device_locations = create_objects(
            user=other_user, object_factory=DeviceLocationFactory
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        assert_object_values_in_response(
            response=response,
            objects=current_user_device_locations,
            field="location",
            exists=True,
        )
        assert_object_values_in_response(
            response=response,
            objects=other_user_device_locations,
            field="location",
            exists=False,
        )


class TestDetailDeviceLocation(TestCase):
    pass


class TestUpdateDeviceLocation(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(user=self.user)

        self.location = DeviceLocationFactory(
            user=self.user,
        )
        self.url = reverse(
            "devices:locations:update", kwargs={"uuid": self.location.uuid}
        )

    def test_anonymous_user_cannot_access_view_pass(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_user_receives_forbidden_response_trying_to_update_another_users_object(
        self,
    ):
        other_user_location = DeviceLocationFactory()

        self.assertTrue(self.user != other_user_location.user)

        new_url = reverse(
            "devices:locations:update", kwargs={"uuid": other_user_location.uuid}
        )

        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 403)

    def test_user_can_access_update_form_for_own_location(self):
        response = self.client.get(self.url)

        values = [
            {
                "value": self.location.location,
                "exists": True,
            },
            {
                "value": "<h1>Update Location Description</h1>",
                "exists": True,
            },
            {
                "value": '<input type="submit" class="btn btn-primary" value="Update Location">',
                "exists": True,
            },
        ]

        self.assertEqual(response.status_code, 200)
        assert_values_in_reponse(response=response, values=values)


class TestDeleteDeviceLocation(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(user=self.user)

    def get_url_response(self, uuid=None, url=None):
        if not url:
            url = reverse("devices:locations:delete", kwargs={"uuid": uuid})

        return self.client.get(url)

    def test_invalid_uuid(self):
        invalid_uuid = "this-is-an-invalid-uuid"
        url = f"/devices/locations/{invalid_uuid}/delete"
        response = self.get_url_response(url=url)

        self.assertEqual(response.status_code, 404)

    def test_valid_location_uuid(self):
        device_location = DeviceLocationFactory(user=self.user)

        response = self.get_url_response(uuid=device_location.uuid)

        values = [
            {
                "value": "<h1>Delete Device Location?</h1>",
                "exists": True,
            },
            {
                "value": device_location.location,
                "exists": True,
            },
            {
                "value": '<input type="submit" class="btn btn-danger" value="Delete">',
                "exists": True,
            },
            {
                "value": '<a href="/devices/locations/" class="btn btn-secondary" role="button">Cancel</a>',
                "exists": True,
            },
        ]

        self.assertEqual(response.status_code, 200)
        assert_values_in_reponse(response=response, values=values)

    def test_user_cannot_delete_other_user_location(self):
        other_user = UserFactory()
        device_location = DeviceLocationFactory(user=other_user)

        response = self.get_url_response(uuid=device_location.uuid)
        self.assertEqual(response.status_code, 404)

    def test_view_deletes_location_and_displays_success_message(self):
        device_location = DeviceLocationFactory(user=self.user)

        response = self.client.get(reverse("devices:locations:list"))

        values = [
            {
                "value": "device locations",
                "exists": True,
            },
            {
                "value": device_location.location,
                "exists": True,
            },
        ]
        assert_values_in_reponse(response, values=values)

        # submit post request to delete object
        response = self.client.post(
            reverse("devices:locations:delete", kwargs={"uuid": device_location.uuid}),
            data={},
            follow=True,
        )
        redirect_url, _ = response.redirect_chain[0]

        values = [
            {
                "value": "device locations",
                "exists": True,
            },
            {
                "value": "The device location has been deleted",
                "exists": True,
            },
            {
                "value": device_location.location,
                "exists": False,
            },
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(redirect_url, reverse("devices:locations:list"))
        assert_values_in_reponse(response, values=values)

    def test_user_cannot_delete_another_users_location_by_posting_form(self):
        device_location = DeviceLocationFactory()

        response = self.client.post(
            reverse("devices:locations:delete", kwargs={"uuid": device_location.uuid}),
            data={},
            follow=True,
        )

        self.assertTrue(device_location.user != self.user)
        self.assertEqual(response.status_code, 404)


class TestAddDeviceLocation(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("devices:locations:add")

        self.client.force_login(user=self.user)

    def test_anonymous_user_cannot_access_view_pass(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_form_is_displayed(self):
        response = self.client.get(self.url)

        values = [
            {
                "value": "add location for devices",
                "exists": True,
            },
            {
                "value": '<input type="submit" class="btn btn-primary" value="add location">',
                "exists": True,
            },
        ]

        self.assertEqual(response.status_code, 200)
        assert_values_in_reponse(response=response, values=values)

    def test_that_submitting_form_results_in_success_message(self):
        form_data = {"location": "Super Duper Test Location"}

        response = self.client.post(self.url, data=form_data, follow=True)

        values = [
            {
                "value": "The new device location has been added - you have been redirected to it",
                "exists": True,
            },
        ]

        self.assertEqual(response.status_code, 200)
        assert_values_in_reponse(response=response, values=values)
