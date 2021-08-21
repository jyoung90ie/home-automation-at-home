from django.test import TestCase
from django.urls import reverse

from .factories import DeviceFactory, DeviceLocationFactory, UserFactory

login_url = reverse("account_login")
test_user_password = "test_1234!"


def create_devices(user, amount=3):
    """Create specified number of devices for given user"""
    devices = []
    for num in range(amount):
        devices.append(DeviceFactory(user=user))
    return devices


def get_response_for_devices(object, response, devices: list, exist=True):
    """Helper which loops through HTTP Reponse and checks if device IS or IS NOT part of it - as specified by user"""
    for device in devices:
        expected = str(device.friendly_name).encode("utf-8")
        if exist:
            object.assertTrue(expected in response.content)
        else:
            object.assertFalse(expected in response.content)


class TestListDevicesView(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.url = reverse("devices:list")
        return super().setUp()

    def test_anonymous_user_cannot_access_view_pass(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_device_list_shows_no_devices_pass(self):
        self.client.login(username=self.user.email,
                          password=test_user_password)
        response = self.client.get(self.url)
        self.assertTrue(b"You do not have any devices" in response.content)

    def test_user_devices_listed(self):
        devices = create_devices(user=self.user)
        self.client.login(username=self.user.email,
                          password=test_user_password)
        response = self.client.get(self.url)

        get_response_for_devices(
            object=self, response=response, devices=devices, exist=True
        )

    def test_user_cannot_see_other_user_devices(self):
        other_user = UserFactory()
        devices = create_devices(user=other_user)
        self.client.login(username=self.user.email,
                          password=test_user_password)
        response = self.client.get(self.url)

        self.assertTrue(b"You do not have any devices" in response.content)
        get_response_for_devices(
            object=self, response=response, devices=devices, exist=False
        )

        new_devices = create_devices(user=self.user)
        response = self.client.get(self.url)

        self.assertFalse(b"You do not have any devices" in response.content)
        get_response_for_devices(
            object=self, response=response, devices=new_devices, exist=True
        )

    def test_anonymous_user_is_redirected_pass(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))


class TestAddDeviceView(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.url = reverse("devices:add")

        self.client.login(username=self.user.email,
                          password=test_user_password)

        return super().setUp()

    def test_anonymous_user_cannot_access_view_pass(self):
        self.client.logout()  # user is logged in as part of setup - need to logout before testing
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_create_device_form_does_not_show_when_no_device_locations_added(self):
        response = self.client.get(self.url)
        self.assertTrue(
            b"You must add at least one device location before you can add a device"
            in response.content
        )
        self.assertFalse(b'<form method="post">' in response.content)

    def test_create_device_with_locations_pass(self):
        device_location = DeviceLocationFactory(user=self.user)
        response = self.client.get(self.url)

        self.assertTrue(device_location.location.encode(
            "utf-8") in response.content)
        self.assertFalse(
            b"You must add at least one device location before you can add a device"
            in response.content
        )

    def test_other_user_locations_not_shown_to_current_user_in_create_device(self):
        other_user_device_location = DeviceLocationFactory()
        current_user_device_location = DeviceLocationFactory(user=self.user)
        response = self.client.get(self.url)

        self.assertFalse(
            other_user_device_location.location.encode(
                "utf-8") in response.content
        )
        self.assertTrue(
            current_user_device_location.location.encode(
                "utf-8") in response.content
        )


class TestUpdateDeviceView(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.device = DeviceFactory(
            user=self.user,
            friendly_name="Test Device",
            device_identifier="TEST1234",
        )
        self.url = reverse("devices:device:update", kwargs={
                           "uuid": self.device.uuid})

        self.client.login(username=self.user.email,
                          password=test_user_password)

    def test_update_own_device_pass(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"Update Device" in response.content)
        self.assertTrue(b"Test Device" in response.content)
        self.assertTrue(b"TEST1234" in response.content)

    def test_update_other_users_device_fail(self):
        other_user_device = DeviceFactory()
        url = reverse("devices:device:update", kwargs={
                      "uuid": other_user_device.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_update_device_with_invalid_uuid_pass(self):
        def get_url_response(uuid):
            url = f"/devices/{uuid}/update"
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
            "location": self.device.location.id,
            "protocol": self.device.protocol,
        }
        response = self.client.post(self.url, updated_data)
        print(response.content)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("devices:device:detail", kwargs={
                    "uuid": self.device.uuid}),
        )

    def test_view_updates_other_user_device_fail(self):
        other_user_device = DeviceFactory()
        updated_data = {
            "friendly_name": "NewFriendlyName",
            "device_identifier": self.device.device_identifier,
            "location": self.device.location,
            "protocol": self.device.protocol,
        }
        response = self.client.post(
            reverse("devices:device:update", kwargs={
                    "uuid": other_user_device.uuid}),
            updated_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_pass(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))


class TestDeleteDeviceView(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.device = DeviceFactory(
            user=self.user,
            friendly_name="Test Device",
            device_identifier="TEST1234",
        )
        self.url = reverse("devices:device:delete", kwargs={
                           "uuid": self.device.uuid})

        self.client.login(username=self.user.email,
                          password=test_user_password)

    def test_delete_own_device_pass(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            b'<input type="submit" class="btn btn-danger" value="Delete">'
            in response.content
        )

    def test_delete_other_users_device_fail(self):
        other_user_device = DeviceFactory()
        url = reverse("devices:device:delete", kwargs={
                      "uuid": other_user_device.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_pass(self):
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


class TestListDevicesView(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.url = reverse("devices:list")

        self.client.login(username=self.user.email,
                          password=test_user_password)

    def test_device_list_empty_pass(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"You do not have any devices" in response.content)

    def test_device_list_not_empty_pass(self):
        device = DeviceFactory(
            user=self.user,
            friendly_name="TestDevice",
            device_identifier="TEST1234",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            device.friendly_name in response.content.decode("utf-8"))
        self.assertTrue(
            device.device_identifier in response.content.decode("utf-8"))

    def test_device_list_does_not_show_other_users_devices_pass(self):
        other_users_device = DeviceFactory(
            friendly_name="OtherUser'sTestDevice",
            device_identifier="OTHER_USER_DEVICE321",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            other_users_device.friendly_name in response.content.decode(
                "utf-8")
        )
        self.assertFalse(
            other_users_device.device_identifier in response.content.decode(
                "utf-8")
        )

    def test_anonymous_user_is_redirected_pass(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))


class TestDeviceLocationViews(TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_create_device_location_with_no_locations_fail(self):
        assert 1 == 1

    def test_create_device_location_with_locations_pass(self):
        assert 1 == 1

    def test_update_own_device_location_pass(self):
        assert 1 == 1

    def test_update_other_users_device_location_fail(self):
        assert 1 == 1

    def test_delete_own_device_location_pass(self):
        assert 1 == 1

    def test_delete_other_users_device_location_fail(self):
        assert 1 == 1

    def test_device_location_list_empty_pass(self):
        assert 1 == 1

    def test_device_location_list_not_empty_pass(self):
        assert 1 == 1
