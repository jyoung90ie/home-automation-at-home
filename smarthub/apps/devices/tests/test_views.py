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


class TestListDevices(TestCase):
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
        self.client.login(username=self.user.email, password=test_user_password)
        response = self.client.get(self.url)
        self.assertTrue(b"You do not have any devices" in response.content)

    def test_user_devices_listed(self):
        devices = create_devices(user=self.user)
        self.client.login(username=self.user.email, password=test_user_password)
        response = self.client.get(self.url)

        get_response_for_devices(
            object=self, response=response, devices=devices, exist=True
        )

    def test_user_cannot_see_other_user_devices(self):
        other_user = UserFactory()
        devices = create_devices(user=other_user)
        self.client.login(username=self.user.email, password=test_user_password)
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

    def test_that_anonymous_users_are_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))


class TestAddDevice(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.url = reverse("devices:add")

        self.client.login(username=self.user.email, password=test_user_password)

        return super().setUp()

    def test_anonymous_user_cannot_access_view_pass(self):
        self.client.logout()  # user is logged in as part of setup - need to logout before testing
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_create_device_form_does_not_show_when_no_device_locations_added(self):
        response = self.client.get(self.url)
        print(response.content.decode("utf-8"))
        self.assertTrue(
            b"You must add at least one device location before you can add a device"
            in response.content
        )
        self.assertFalse(b'<form method="post">' in response.content)

    def test_create_device_with_locations_pass(self):
        device_location = DeviceLocationFactory(user=self.user)
        response = self.client.get(self.url)

        self.assertTrue(device_location.location.encode("utf-8") in response.content)
        self.assertFalse(
            b"You must add at least one device location before you can add a device"
            in response.content
        )

    def test_other_user_locations_not_shown_to_current_user_in_create_device(self):
        other_user_device_location = DeviceLocationFactory()
        current_user_device_location = DeviceLocationFactory(user=self.user)
        response = self.client.get(self.url)

        self.assertFalse(
            other_user_device_location.location.encode("utf-8") in response.content
        )
        self.assertTrue(
            current_user_device_location.location.encode("utf-8") in response.content
        )


class TestUpdateDevice(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.device = DeviceFactory(
            user=self.user,
            friendly_name="Test Device",
            device_identifier="TEST1234",
        )
        self.url = reverse("devices:device:update", kwargs={"uuid": self.device.uuid})

        self.client.login(username=self.user.email, password=test_user_password)

    def test_that_update_view_populates_device_details(self):
        response = self.client.get(self.url)

        content = response.content.decode("utf-8").lower()

        self.assertEqual(response.status_code, 200)
        self.assertTrue("update device" in content)
        self.assertTrue(self.device.friendly_name.lower() in content)
        self.assertTrue(self.device.device_identifier.lower() in content)
        self.assertTrue(self.device.location.location.lower() in content)

    def test_that_current_user_cannot_view_update_form_for_another_users_device(self):
        other_user_device = DeviceFactory()
        url = reverse("devices:device:update", kwargs={"uuid": other_user_device.uuid})
        response = self.client.get(url)

        print(response.content.decode("utf-8"))

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
            "location": self.device.location.id,
            "protocol": self.device.protocol,
        }
        response = self.client.post(self.url, updated_data)
        print(response.content)
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
        self.user.set_password(test_user_password)
        self.user.save()

        self.device = DeviceFactory(
            user=self.user,
            friendly_name="Test Device",
            device_identifier="TEST1234",
        )
        self.url = reverse("devices:device:delete", kwargs={"uuid": self.device.uuid})

        self.client.login(username=self.user.email, password=test_user_password)

    def test_delete_own_device_pass(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            b'<input type="submit" class="btn btn-danger" value="Delete">'
            in response.content
        )

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


class TestListDevices(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.url = reverse("devices:list")

        self.client.login(username=self.user.email, password=test_user_password)

    def test_when_no_devices_exist_message_is_shown(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"You do not have any devices" in response.content)

    def test_that_device_appears_in_device_list(self):
        device = DeviceFactory(
            user=self.user,
            friendly_name="TestDevice",
            device_identifier="TEST1234",
        )

        response = self.client.get(self.url)
        content = response.content.decode("utf-8").lower()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(device.friendly_name.lower() in content)
        self.assertTrue(device.device_identifier.lower() in content)

    def test_that_another_users_devices_do_not_appear_in_current_users_list(self):
        other_users_device = DeviceFactory(
            friendly_name="OtherUser'sTestDevice",
            device_identifier="OTHER_USER_DEVICE321",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8").lower()
        self.assertFalse(other_users_device.friendly_name.lower() in content)
        self.assertFalse(other_users_device.device_identifier.lower() in content)

    def test_anonymous_users_are_redirected_to_login_page(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))


class TestDeviceLocationList(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.client.login(username=self.user.email, password=test_user_password)

        self.url = reverse("devices:locations:list")

    def test_user_is_shown_message_when_no_locations(self):
        response = self.client.get(self.url)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(b"You have not added any locations" in response.content)
        self.assertFalse(b"devicelocation-row" in response.content)

    def test_anonymous_users_are_redirected_to_login_page(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_location_appears_in_list_when_added(self):
        location = DeviceLocationFactory(user=self.user)

        response = self.client.get(self.url)
        content = response.content.decode("utf-8").lower()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(location.location in content)
        self.assertTrue("total devices" in content)
        self.assertTrue("total linked devices" in content)
        self.assertTrue("created on" in content)
        self.assertTrue("options" in content)

    def test_that_another_users_locations_do_not_appear(self):
        current_user_location = DeviceLocationFactory(user=self.user)
        other_user = UserFactory()
        other_user_location_1 = DeviceLocationFactory(user=other_user)
        other_user_location_2 = DeviceLocationFactory(user=other_user)

        response = self.client.get(self.url)
        content = response.content.decode("utf-8").lower()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(current_user_location.location in content)
        self.assertFalse(other_user_location_1.location in content)
        self.assertFalse(other_user_location_2.location in content)


class TestAddDeviceLocation(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.url = reverse("devices:locations:add")

        self.client.login(username=self.user.email, password=test_user_password)

        return super().setUp()

    def test_anonymous_user_cannot_access_view_pass(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_form_is_displayed(self):
        response = self.client.get(self.url)
        content = response.content.decode("utf-8").lower()

        self.assertTrue("add location for devices" in content)
        self.assertTrue(
            '<input type="submit" class="btn btn-primary" value="add location">'
            in content
        )

    def test_that_submitting_form_results_in_success_message(self):
        form_data = {"location": "Super Duper Test Location"}
        response = self.client.post(self.url, data=form_data, follow=True)

        print(response.content.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            b"The new device location has been added - you have been redirected to it"
            in response.content
        )


class TestUpdateDeviceLocation(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.user.set_password(test_user_password)
        self.user.save()

        self.location = DeviceLocationFactory(
            user=self.user,
        )
        self.url = reverse(
            "devices:locations:update", kwargs={"uuid": self.location.uuid}
        )

        self.client.login(username=self.user.email, password=test_user_password)

    def test_anonymous_user_cannot_access_view_pass(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(login_url))

    def test_user_receives_forbidden_message_trying_to_update_another_users_object(
        self,
    ):
        other_user_location = DeviceLocationFactory()

        self.assertTrue(self.user != other_user_location.user)
        print("user", self.user)
        print("other user", other_user_location.user)
        print("location obj", other_user_location, dir(other_user_location))

        new_url = reverse(
            "devices:locations:update", kwargs={"uuid": other_user_location.uuid}
        )

        response = self.client.get(new_url)

        self.assertEqual(response.status_code, 403)

    def test_user_can_access_update_form_for_own_location(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.location.location in response.content.decode("utf-8"))

    # def test_that_update_view_populates_device_details(self):
    #     response = self.client.get(self.url)

    #     content = response.content.decode("utf-8").lower()

    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue("update device" in content)
    #     self.assertTrue(self.device.friendly_name.lower() in content)
    #     self.assertTrue(self.device.device_identifier.lower() in content)
    #     self.assertTrue(self.device.location.location.lower() in content)

    # def test_that_current_user_cannot_view_update_form_for_another_users_device(self):
    #     other_user_device = DeviceFactory()
    #     url = reverse("devices:device:update", kwargs={"uuid": other_user_device.uuid})
    #     response = self.client.get(url)

    #     print(response.content.decode("utf-8"))

    #     self.assertFalse(other_user_device.user == self.user)
    #     self.assertEqual(response.status_code, 403)

    # def test_update_device_with_invalid_uuid_pass(self):
    #     def get_url_response(uuid):
    #         url = f"/devices/{uuid}/update/"
    #         return self.client.get(url)

    #     # make sure valid uuid returns 200 before testing - ensuring hardcoded URL is valid
    #     valid_uuid = self.device.uuid
    #     response = get_url_response(valid_uuid)
    #     self.assertEqual(response.status_code, 200)

    #     # repeat for invalid
    #     invalid_uuid = "this-is-an-invalid-uuid"
    #     response = get_url_response(invalid_uuid)
    #     self.assertEqual(response.status_code, 404)

    # def test_view_updates_own_device_pass(self):
    #     new_location = DeviceLocationFactory(user=self.user)

    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)

    #     updated_data = {
    #         "friendly_name": "NewFriendlyName",
    #         "device_identifier": self.device.device_identifier,
    #         "location": self.device.location.id,
    #         "protocol": self.device.protocol,
    #     }
    #     response = self.client.post(self.url, updated_data)
    #     print(response.content)
    #     self.assertEqual(response.status_code, 302)
    #     self.assertEqual(
    #         response.url,
    #         reverse("devices:device:detail", kwargs={"uuid": self.device.uuid}),
    #     )

    # def test_that_another_user_cannot_update_current_users_device(self):
    #     other_user_device = DeviceFactory()
    #     updated_data = {
    #         "friendly_name": "NewFriendlyName",
    #         "device_identifier": self.device.device_identifier,
    #         "location": self.device.location,
    #         "protocol": self.device.protocol,
    #     }
    #     response = self.client.post(
    #         reverse("devices:device:update", kwargs={"uuid": other_user_device.uuid}),
    #         updated_data,
    #         follow=True,
    #     )
    #     self.assertFalse(other_user_device.user == self.user)
    #     self.assertEqual(response.status_code, 403)

    # def test_that_anonymous_users_are_redirected_to_login(self):
    #     self.client.logout()
    #     response = self.client.get(self.url)

    #     self.assertEqual(response.status_code, 302)
    #     self.assertTrue(response.url.startswith(login_url))


# class TestDeleteDevice(TestCase):
#     def setUp(self) -> None:
#         self.user = UserFactory()
#         self.user.set_password(test_user_password)
#         self.user.save()

#         self.device = DeviceFactory(
#             user=self.user,
#             friendly_name="Test Device",
#             device_identifier="TEST1234",
#         )
#         self.url = reverse("devices:device:delete", kwargs={"uuid": self.device.uuid})

#         self.client.login(username=self.user.email, password=test_user_password)

#     def test_delete_own_device_pass(self):
#         response = self.client.get(self.url)

#         self.assertEqual(response.status_code, 200)
#         self.assertTrue(
#             b'<input type="submit" class="btn btn-danger" value="Delete">'
#             in response.content
#         )

#     def test_delete_other_users_device_fail(self):
#         other_user_device = DeviceFactory()
#         url = reverse("devices:device:delete", kwargs={"uuid": other_user_device.uuid})
#         response = self.client.get(url)

#         self.assertEqual(response.status_code, 403)

#     def test_anonymous_user_is_redirected_to_login_page(self):
#         self.client.logout()
#         response = self.client.get(self.url)

#         self.assertEqual(response.status_code, 302)
#         self.assertTrue(response.url.startswith(login_url))

#     def test_delete_view_deletes_device(self):
#         response = self.client.post(self.url, data={})
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(response.url, reverse("devices:list"))

#         # check if device page exists
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 404)
