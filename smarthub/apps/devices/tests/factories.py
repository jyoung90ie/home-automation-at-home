import factory
from factory import fuzzy
from .. import models
from ...users.tests.factories import UserFactory
from django.db.models.signals import post_save


@factory.django.mute_signals(post_save)
class DeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Device

    uuid = factory.Faker("uuid4")
    friendly_name = factory.Faker("name")
    device_identifier = factory.Faker("catch_phrase")
    user = factory.SubFactory(UserFactory)
    protocol = fuzzy.FuzzyChoice(models.Device.DeviceProtocol.values)
    location = factory.SubFactory(
        "apps.devices.tests.factories.DeviceLocationFactory",
        device=None,
        user=factory.SelfAttribute("..user"),
    )


@factory.django.mute_signals(post_save)
class DeviceLocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DeviceLocation

    location = factory.Faker("city")
    device = factory.SubFactory(DeviceFactory)
    user = factory.SubFactory(UserFactory)