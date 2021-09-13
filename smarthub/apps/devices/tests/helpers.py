"""Testing helper methods"""
from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from django.test import TestCase

from factory.base import Factory


class TestCaseWithHelpers(TestCase):
    def create_objects(
        self, user: get_user_model(), object_factory: Factory, amount: int = 3
    ) -> list:
        """Create objects which are attached to the specified user for given user"""
        object_list = []
        for num in range(amount):
            object_list.append(object_factory(user=user))
        return object_list

    def assert_object_values_in_response(
        self, response: HttpResponse, objects: list, field: str, exists: bool = True
    ) -> None:
        """Helper which loops through HTTP Reponse.

        Returns True if object value exists in response, otherwise False"""

        content = response.content.decode("utf-8").lower()

        for obj in objects:
            expected = str(getattr(obj, field)).lower()
            with self.subTest(expected=expected):

                if exists:
                    self.assertTrue(expected in content)
                else:
                    self.assertFalse(expected in content)

    def assert_values_in_reponse(
        self, response: HttpResponse, values: list[dict[str, bool]]
    ) -> None:
        content = response.content.decode("utf-8").lower()

        for _dict in values:
            value = str(_dict["value"]).lower()
            exists = bool(_dict["exists"])
            with self.subTest(value=value):

                if exists:
                    self.assertTrue(value in content)
                else:
                    self.assertFalse(value in content)
