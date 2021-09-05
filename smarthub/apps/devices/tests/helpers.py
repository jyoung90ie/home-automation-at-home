"""Testing helper methods"""
from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from factory.base import Factory


def create_objects(user: get_user_model(), object_factory: Factory, amount: int = 3):
    """Create objects which are attached to the specified user for given user"""
    object_list = []
    for num in range(amount):
        object_list.append(object_factory(user=user))
    return object_list


def assert_object_values_in_response(
    response: HttpResponse, objects: list, field: str, exists: bool = True
) -> bool:
    """Helper which loops through HTTP Reponse.

    Returns True if object value exists in response, otherwise False"""

    content = response.content.decode("utf-8").lower()

    for obj in objects:
        expected = str(getattr(obj, field)).lower()

        if exists:
            assert expected in content
        else:
            assert expected not in content


def assert_values_in_reponse(
    response: HttpResponse, values: list[dict[str, bool]]
) -> bool:
    content = response.content.decode("utf-8").lower()

    for _dict in values:
        value = str(_dict["value"]).lower()
        exists = bool(_dict["exists"])

        if exists:
            assert value in content
        else:
            assert value not in content
