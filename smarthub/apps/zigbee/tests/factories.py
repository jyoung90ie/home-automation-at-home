import factory
from factory import fuzzy
from django.db.models.signals import post_save

from .. import models


@factory.django.mute_signals(post_save)
class ZigbeeDeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ZigbeeDevice

    uuid = factory.Faker("uuid4")
    device = factory.SubFactory("apps.devices.tests.factories.DeviceFactory")
    friendly_name = factory.Faker("name")
    ieee_address = factory.Faker("ssn")
    description = factory.Faker("sentence")
    vendor = factory.Sequence(lambda n: "vendor %s" % n)
    model = factory.Faker("catch_phrase")
    model_id = fuzzy.FuzzyText(length=6, prefix="MODEL-")
    power_source = fuzzy.FuzzyChoice(["Battery", "Mains"])


@factory.django.mute_signals(post_save)
class ZigbeeMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ZigbeeMessage

    uuid = factory.Faker("uuid4")
    zigbee_device = factory.SubFactory(ZigbeeDeviceFactory)
    topic = factory.SelfAttribute("zigbee_device.friendly_name")


@factory.django.mute_signals(post_save)
class ZigbeeLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ZigbeeLog

    uuid = factory.Faker("uuid4")
    broker_message = factory.SubFactory(ZigbeeMessageFactory)
    metadata_type = fuzzy.FuzzyChoice(
        [
            "linkquality",
            "state",
            "temperature",
            "humidity",
            "battery_low",
            "battery",
            "occupancy",
        ]
    )
    metadata_value = fuzzy.FuzzyChoice(
        [
            "on",
            "off",
            "true",
            "false",
            fuzzy.FuzzyInteger(low=0, high=100),
        ]
    )
