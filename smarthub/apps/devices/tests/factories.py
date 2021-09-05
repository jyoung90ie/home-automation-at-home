from django.contrib.contenttypes.models import ContentType
import factory
from django.db.models.signals import post_save

from ...users.tests.factories import UserFactory
from .. import models
from ...zigbee.tests.factories import ZigbeeDeviceFactory


@factory.django.mute_signals(post_save)
class DeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Device

    uuid = factory.Faker("uuid4")
    friendly_name = factory.Faker("name")
    device_identifier = factory.Faker("isbn")
    user = factory.SubFactory(UserFactory)
    protocol = factory.fuzzy.FuzzyChoice(models.DeviceProtocol.values)
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
    user = factory.SubFactory(UserFactory)


class DeviceStateFactory(factory.django.DjangoModelFactory):
    class Meta:
        exclude = ["content_object"]
        abstract = True

    device_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.content_object)
    )
    device_object_id = factory.SelfAttribute("content_object.id")
    name = factory.Faker("name")
    command = "state"
    command_value = factory.fuzzy.FuzzyChoice(["on", "off", "toggle"])


class ZigbeeDeviceStateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DeviceState

    content_object = factory.SubFactory(ZigbeeDeviceFactory)
